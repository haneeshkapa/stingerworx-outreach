"""
WebRTC Browser Streaming Module
Provides real-time video streaming of Playwright browser automation via aiortc
"""
import asyncio
import base64
import logging
from typing import Optional, AsyncIterator
from datetime import datetime
import numpy as np
from PIL import Image
import io

from playwright.async_api import async_playwright, Page, Browser
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

logger = logging.getLogger(__name__)

class FrameProducer:
    """
    Captures frames from a Playwright browser session.
    Uses Playwright's screenshot API to capture frames at target FPS.
    """
    
    def __init__(self, target_fps: int = 10):
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.running = False
        
    async def start(self, url: str = "https://www.google.com", headless: bool = False):
        """Start Playwright browser and navigate to URL"""
        logger.info(f"🎬 Starting browser for WebRTC stream (headless={headless})")
        
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
        await self.page.goto(url)
        
        self.running = True
        logger.info(f"✅ Browser started and navigated to {url}")
        
    async def capture_frame(self) -> bytes:
        """Capture a single frame as JPEG bytes"""
        if not self.page:
            raise RuntimeError("Browser not started")
            
        screenshot_bytes = await self.page.screenshot(type='jpeg', quality=80)
        return screenshot_bytes
    
    async def frame_iterator(self) -> AsyncIterator[bytes]:
        """Async generator that yields frames at target FPS"""
        while self.running:
            try:
                frame_bytes = await self.capture_frame()
                yield frame_bytes
                await asyncio.sleep(self.frame_interval)
            except Exception as e:
                logger.error(f"Frame capture error: {e}")
                break
    
    async def navigate(self, url: str):
        """Navigate browser to new URL"""
        if self.page:
            logger.info(f"🔗 Navigating to {url}")
            await self.page.goto(url)
    
    async def fill_and_search(self, selector: str, text: str):
        """Helper to fill input and press Enter"""
        if self.page:
            await self.page.fill(selector, text)
            await self.page.press(selector, 'Enter')
            await asyncio.sleep(2)
    
    async def stop(self):
        """Stop browser and cleanup"""
        self.running = False
        
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
        logger.info("🛑 Browser stopped")


class BrowserVideoStreamTrack(VideoStreamTrack):
    """
    aiortc VideoStreamTrack that streams frames from FrameProducer.
    Converts JPEG screenshots to VideoFrame objects for WebRTC transmission.
    """
    
    def __init__(self, frame_producer: FrameProducer):
        super().__init__()
        self.frame_producer = frame_producer
        self.counter = 0
        
    async def recv(self):
        """
        Called by aiortc to get next video frame.
        Converts JPEG bytes to numpy array to VideoFrame.
        """
        pts, time_base = await self.next_timestamp()
        
        try:
            frame_bytes = await self.frame_producer.capture_frame()
            
            # Convert JPEG bytes to PIL Image to numpy array
            image = Image.open(io.BytesIO(frame_bytes))
            img_array = np.array(image)
            
            # Convert RGB to BGR for VideoFrame (if needed)
            if img_array.shape[2] == 3:
                img_array = img_array[:, :, ::-1]
            
            # Create VideoFrame
            frame = VideoFrame.from_ndarray(img_array, format='bgr24')
            frame.pts = pts
            frame.time_base = time_base
            
            self.counter += 1
            return frame
            
        except Exception as e:
            logger.error(f"Frame conversion error: {e}")
            raise


class BrowserStreamManager:
    """
    Manages WebRTC peer connections and Playwright browser sessions.
    Maps session_id → (RTCPeerConnection, FrameProducer)
    """
    
    def __init__(self):
        self.sessions = {}
        self.relay = MediaRelay()
        
    async def create_session(self, session_id: str, headless: bool = False) -> RTCPeerConnection:
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
