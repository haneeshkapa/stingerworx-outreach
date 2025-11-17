"""
WebRTC Browser Streaming Module using CDP (Chrome DevTools Protocol)
Provides real-time video streaming via CDP's Page.startScreencast for efficient DOM mirroring
"""
import asyncio
import base64
import logging
from typing import Optional
from datetime import datetime
import numpy as np
from PIL import Image
import io
from collections import deque

from playwright.async_api import async_playwright, Page, Browser, CDPSession
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

logger = logging.getLogger(__name__)

class CDPFrameProducer:
    """
    Captures frames from browser using Chrome DevTools Protocol (CDP) screencast.
    Much more efficient than screenshot-based approach - uses CDP Page.startScreencast.
    """
    
    def __init__(self, target_fps: int = 15, max_buffer_size: int = 30):
        self.target_fps = target_fps
        self.max_buffer_size = max_buffer_size
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.cdp_session: Optional[CDPSession] = None
        self.playwright = None
        self.running = False
        
        # Frame buffer for async decoupling
        self.frame_buffer = deque(maxlen=max_buffer_size)
        self.latest_frame: Optional[bytes] = None
        self.frame_lock = asyncio.Lock()
        
    async def start(self, url: str = "https://www.google.com", headless: bool = True):
        """Start Playwright browser with CDP session and begin screencast"""
        logger.info(f"🎬 Starting CDP browser stream (headless={headless}, {self.target_fps} FPS)")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        # Create page with specific viewport for consistent streaming
        self.page = await self.browser.new_page(viewport={'width': 1280, 'height': 720})
        
        # Create CDP session for direct protocol access
        self.cdp_session = await self.page.context.new_cdp_session(self.page)
        
        # Set up screencast frame handler
        self.cdp_session.on("Page.screencastFrame", self._handle_screencast_frame)
        
        # Start screencast with CDP
        await self.cdp_session.send("Page.startScreencast", {
            "format": "jpeg",
            "quality": 80,
            "maxWidth": 1280,
            "maxHeight": 720,
            "everyNthFrame": max(1, int(30 / self.target_fps))  # Throttle to target FPS
        })
        
        # Navigate to initial URL
        await self.page.goto(url)
        
        self.running = True
        logger.info(f"✅ CDP screencast started at {url}")
        
    async def _handle_screencast_frame(self, params: dict):
        """
        CDP event handler for Page.screencastFrame events.
        Receives frames directly from Chrome compositor.
        """
        try:
            # Extract frame data
            session_id = params.get("sessionId")
            frame_data = params.get("data")  # Base64 encoded JPEG
            
            # Acknowledge frame (required by CDP protocol)
            if session_id and self.cdp_session:
                await self.cdp_session.send("Page.screencastFrameAck", {"sessionId": session_id})
            
            # Decode base64 frame
            if frame_data:
                frame_bytes = base64.b64decode(frame_data)
                
                async with self.frame_lock:
                    self.latest_frame = frame_bytes
                    self.frame_buffer.append(frame_bytes)
                
        except Exception as e:
            logger.error(f"Error handling CDP screencast frame: {e}")
    
    async def get_latest_frame(self) -> Optional[bytes]:
        """Get the most recent frame from CDP screencast"""
        async with self.frame_lock:
            return self.latest_frame
    
    async def navigate(self, url: str):
        """Navigate browser to new URL"""
        if self.page:
            logger.info(f"🔗 Navigating to {url}")
            await self.page.goto(url, wait_until="domcontentloaded")
    
    async def fill_and_search(self, selector: str, text: str):
        """Helper to fill input and press Enter"""
        if self.page:
            await self.page.fill(selector, text)
            await self.page.press(selector, 'Enter')
            await asyncio.sleep(1.5)
    
    async def stop(self):
        """Stop CDP screencast and cleanup"""
        self.running = False
        
        try:
            if self.cdp_session:
                await self.cdp_session.send("Page.stopScreencast")
                await self.cdp_session.detach()
        except Exception as e:
            logger.error(f"Error stopping CDP session: {e}")
        
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        logger.info("🛑 CDP browser stream stopped")


class CDPVideoStreamTrack(VideoStreamTrack):
    """
    aiortc VideoStreamTrack that streams frames from CDP screencast.
    Efficiently converts CDP JPEG frames to VideoFrame objects.
    """
    
    def __init__(self, frame_producer: CDPFrameProducer):
        super().__init__()
        self.frame_producer = frame_producer
        self.counter = 0
        self.placeholder_frame = None
        
    def _create_placeholder_frame(self):
        """Create a black placeholder frame for when no CDP frames available yet"""
        img_array = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame = VideoFrame.from_ndarray(img_array, format='bgr24')
        return frame
        
    async def recv(self):
        """
        Called by aiortc to get next video frame.
        Returns CDP screencast frame as VideoFrame.
        """
        pts, time_base = await self.next_timestamp()
        
        try:
            # Get latest frame from CDP
            frame_bytes = await self.frame_producer.get_latest_frame()
            
            if not frame_bytes:
                # No frame available yet, return placeholder
                if not self.placeholder_frame:
                    self.placeholder_frame = self._create_placeholder_frame()
                frame = self.placeholder_frame
            else:
                # Convert JPEG bytes to PIL Image to numpy array
                image = Image.open(io.BytesIO(frame_bytes))
                img_array = np.array(image)
                
                # Convert RGB to BGR for VideoFrame
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    img_array = img_array[:, :, ::-1]
                
                # Create VideoFrame
                frame = VideoFrame.from_ndarray(img_array, format='bgr24')
            
            frame.pts = pts
            frame.time_base = time_base
            
            self.counter += 1
            return frame
            
        except Exception as e:
            logger.error(f"Frame conversion error: {e}")
            # Return placeholder on error
            if not self.placeholder_frame:
                self.placeholder_frame = self._create_placeholder_frame()
            frame = self.placeholder_frame
            frame.pts = pts
            frame.time_base = time_base
            return frame


class BrowserStreamManager:
    """
    Manages WebRTC peer connections and CDP browser sessions.
    Maps session_id → (RTCPeerConnection, CDPFrameProducer)
    """
    
    def __init__(self):
        self.sessions = {}
        self.relay = MediaRelay()
        
    async def create_session(self, session_id: str, headless: bool = True) -> RTCPeerConnection:
        """
        Create new WebRTC session with CDP browser stream.
        Returns RTCPeerConnection ready for offer/answer exchange.
        """
        logger.info(f"🎥 Creating CDP WebRTC session: {session_id}")
        
        # Create CDP frame producer and start browser
        frame_producer = CDPFrameProducer(target_fps=15)
        await frame_producer.start(url="https://www.google.com", headless=headless)
        
        # Create WebRTC peer connection
        pc = RTCPeerConnection()
        
        # Add video track with CDP stream
        video_track = CDPVideoStreamTrack(frame_producer)
        pc.addTrack(video_track)
        
        # Store session
        self.sessions[session_id] = {
            'pc': pc,
            'producer': frame_producer,
            'track': video_track
        }
        
        # Setup cleanup on connection state change
        @pc.on("connectionstatechange")
        async def on_state_change():
            logger.info(f"WebRTC state: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.close_session(session_id)
        
        return pc
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    async def navigate_session(self, session_id: str, url: str):
        """Navigate browser in existing session"""
        session = self.sessions.get(session_id)
        if session:
            await session['producer'].navigate(url)
    
    async def search_session(self, session_id: str, query: str):
        """Perform Google search in session"""
        session = self.sessions.get(session_id)
        if session:
            await session['producer'].navigate("https://www.google.com")
            await asyncio.sleep(1)
            await session['producer'].fill_and_search('textarea[name="q"]', query)
    
    async def close_session(self, session_id: str):
        """Close and cleanup session"""
        session = self.sessions.get(session_id)
        if session:
            await session['producer'].stop()
            await session['pc'].close()
            del self.sessions[session_id]
            logger.info(f"🗑️ Closed CDP session: {session_id}")
    
    async def close_all(self):
        """Close all active sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# Global instance
stream_manager = BrowserStreamManager()
