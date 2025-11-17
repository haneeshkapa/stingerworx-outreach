"""
WebRTC Browser Streaming Module using optimized screenshot approach
Provides real-time video streaming via Playwright screenshots (optimized for reliability)
"""
import asyncio
import logging
from typing import Optional
import numpy as np
from PIL import Image
import io
from collections import deque

from playwright.async_api import async_playwright, Page, Browser
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

logger = logging.getLogger(__name__)

class FrameProducer:
    """
    Captures frames from browser using optimized screenshot approach.
    Reliable and simple - works in all environments.
    """
    
    def __init__(self, target_fps: int = 10):
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.running = False
        self.latest_frame: Optional[bytes] = None
        self.frame_lock = asyncio.Lock()
        self._capture_task = None
        
    async def start(self, url: str = "https://www.google.com", headless: bool = True):
        """Start Playwright browser"""
        logger.info(f"🎬 Starting browser stream (headless={headless}, {self.target_fps} FPS)")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        
        self.page = await self.browser.new_page(viewport={'width': 1280, 'height': 720})
        
        # Navigate with timeout
        try:
            await asyncio.wait_for(
                self.page.goto(url, wait_until="domcontentloaded"),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Navigation timeout, continuing anyway")
        
        self.running = True
        logger.info(f"✅ Browser stream started")
    
    async def get_latest_frame(self) -> Optional[bytes]:
        """Capture and return a frame on-demand"""
        if not self.page or not self.running:
            return None
        
        try:
            frame_bytes = await asyncio.wait_for(
                self.page.screenshot(type='jpeg', quality=75),
                timeout=2.0
            )
            async with self.frame_lock:
                self.latest_frame = frame_bytes
            return frame_bytes
        except (asyncio.TimeoutError, Exception) as e:
            logger.error(f"Frame capture error: {e}")
            return self.latest_frame  # Return last known frame
    
    async def navigate(self, url: str):
        """Navigate browser to new URL"""
        if self.page:
            logger.info(f"🔗 Navigating to {url}")
            await self.page.goto(url, wait_until="domcontentloaded")
    
    async def fill_and_search(self, selector: str, text: str):
        """Helper to fill input and press Enter"""
        if self.page:
            try:
                await self.page.fill(selector, text, timeout=5000)
                await self.page.press(selector, 'Enter')
                await asyncio.sleep(1.5)
            except Exception as e:
                logger.error(f"Search error: {e}")
    
    async def stop(self):
        """Stop browser and cleanup"""
        self.running = False
        
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        logger.info("🛑 Browser stream stopped")


class BrowserVideoStreamTrack(VideoStreamTrack):
    """
    aiortc VideoStreamTrack that streams frames from FrameProducer.
    Converts JPEG screenshots to VideoFrame objects.
    """
    
    def __init__(self, frame_producer: FrameProducer):
        super().__init__()
        self.frame_producer = frame_producer
        self.counter = 0
        self.placeholder_frame = None
        
    def _create_placeholder_frame(self):
        """Create a black placeholder frame"""
        img_array = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame = VideoFrame.from_ndarray(img_array, format='bgr24')
        return frame
        
    async def recv(self):
        """
        Called by aiortc to get next video frame.
        Returns latest frame as VideoFrame.
        """
        pts, time_base = await self.next_timestamp()
        
        try:
            frame_bytes = await self.frame_producer.get_latest_frame()
            
            if not frame_bytes:
                if not self.placeholder_frame:
                    self.placeholder_frame = self._create_placeholder_frame()
                frame = self.placeholder_frame
            else:
                image = Image.open(io.BytesIO(frame_bytes))
                img_array = np.array(image)
                
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    img_array = img_array[:, :, ::-1]
                
                frame = VideoFrame.from_ndarray(img_array, format='bgr24')
            
            frame.pts = pts
            frame.time_base = time_base
            
            self.counter += 1
            return frame
            
        except Exception as e:
            logger.error(f"Frame conversion error: {e}")
            if not self.placeholder_frame:
                self.placeholder_frame = self._create_placeholder_frame()
            frame = self.placeholder_frame
            frame.pts = pts
            frame.time_base = time_base
            return frame


class BrowserStreamManager:
    """
    Manages WebRTC peer connections and browser sessions.
    Maps session_id → (RTCPeerConnection, FrameProducer)
    """
    
    def __init__(self):
        self.sessions = {}
        self.relay = MediaRelay()
        
    async def create_session(self, session_id: str, headless: bool = True) -> RTCPeerConnection:
        """
        Create new WebRTC session with browser stream.
        Returns RTCPeerConnection ready for offer/answer exchange.
        """
        logger.info(f"🎥 Creating WebRTC session: {session_id}")
        
        # Create frame producer and start browser
        frame_producer = FrameProducer(target_fps=10)
        await frame_producer.start(url="https://www.google.com", headless=headless)
        
        # Create WebRTC peer connection
        pc = RTCPeerConnection()
        
        # Add video track
        video_track = BrowserVideoStreamTrack(frame_producer)
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
            logger.info(f"🗑️ Closed session: {session_id}")
    
    async def close_all(self):
        """Close all active sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# Global instance
stream_manager = BrowserStreamManager()
