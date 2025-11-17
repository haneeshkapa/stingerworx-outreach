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
import tempfile
import shutil
from pathlib import Path
from collections import deque

from playwright.async_api import async_playwright, Page, Browser
from aiortc import (
    RTCPeerConnection,
    RTCSessionDescription,
    VideoStreamTrack,
    RTCIceServer,
    RTCConfiguration,
)
from aiortc.contrib.media import MediaRelay
from av import VideoFrame

logger = logging.getLogger(__name__)
NOPECHA_EXTENSION_PATH = Path(__file__).resolve().parent / "nopecha-extension" / "dist" / "chrome"
ICE_SERVERS = RTCConfiguration(iceServers=[
    RTCIceServer(urls=["stun:stun.l.google.com:19302"]),
    RTCIceServer(
        urls=[
            "turn:openrelay.metered.ca:80",
            "turn:openrelay.metered.ca:443",
            "turn:openrelay.metered.ca:443?transport=tcp",
        ],
        username="openrelayproject",
        credential="openrelayproject",
    ),
])

class FrameProducer:
    """
    Captures frames from browser using optimized screenshot approach.
    Reliable and simple - works in all environments.
    """
    
    def __init__(self, target_fps: int = 10, extension_path: Optional[Path] = None):
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        self.browser: Optional[Browser] = None
        self.context = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.running = False
        self.latest_frame: Optional[bytes] = None
        self.frame_lock = asyncio.Lock()
        self._capture_task = None
        self.extension_path = extension_path
        self.user_data_dir: Optional[Path] = None
        
    async def start(self, url: str = "https://www.google.com", headless: bool = True):
        """Start Playwright browser"""
        logger.info(f"🎬 Starting browser stream (headless={headless}, {self.target_fps} FPS)")
        
        use_extension = False
        extension_path = self.extension_path or NOPECHA_EXTENSION_PATH
        if extension_path and extension_path.exists():
            use_extension = True
            logger.info(f"🧩 Loading NopeCHA extension from {extension_path}")
        elif extension_path:
            logger.warning(f"⚠️ NopeCHA extension path missing: {extension_path}")

        self.playwright = await async_playwright().start()
        launch_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
        ]

        if use_extension:
            headless = False  # Chromium extensions need headful mode
            launch_args.extend([
                f'--disable-extensions-except={extension_path}',
                f'--load-extension={extension_path}',
            ])

            # Persistent context required to load extensions
            self.user_data_dir = self.user_data_dir or Path(tempfile.mkdtemp(prefix="pw-nopecha-"))
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=headless,
                args=launch_args,
                viewport={'width': 1280, 'height': 720},
            )
            pages = self.context.pages
            self.page = pages[0] if pages else await self.context.new_page()
        else:
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=launch_args,
            )
            self.context = await self.browser.new_context(viewport={'width': 1280, 'height': 720})
            self.page = await self.context.new_page()
        
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
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        if self.user_data_dir:
            shutil.rmtree(self.user_data_dir, ignore_errors=True)
            
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
        extension_path = NOPECHA_EXTENSION_PATH if NOPECHA_EXTENSION_PATH.exists() else None
        frame_producer = FrameProducer(target_fps=10, extension_path=extension_path)
        await frame_producer.start(
            url="https://www.google.com",
            headless=headless if extension_path is None else False
        )
        
        # Create WebRTC peer connection
        pc = RTCPeerConnection(ICE_SERVERS)
        
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

    async def crawl_state(self, session_id: str, state_code: str):
        """
        Perform a visible crawl step for a state:
        - Google search for "{state} class 3 sot firearms dealer"
        - Move mouse around results
        - Click first organic result if present
        """
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")

        producer: FrameProducer = session['producer']
        page = producer.page
        if not page:
            raise ValueError("Browser page not ready")

        query = f"{state_code} class 3 sot firearms dealer"
        logger.info(f"🕷️ Crawling for state {state_code}: {query}")
        try:
            await producer.navigate("https://www.google.com")
            await asyncio.sleep(1)
            await producer.fill_and_search('textarea[name=\"q\"]', query)

            # Gentle pointer movement to make it visible
            await page.mouse.move(200, 300, steps=20)
            await page.mouse.move(900, 500, steps=30)
            await page.mouse.move(400, 200, steps=15)

            # Scroll a bit
            await page.mouse.wheel(0, 600)
            await asyncio.sleep(0.5)

            # Click first organic result if it exists
            first_result = page.locator('a h3').first
            if await first_result.count() > 0:
                box = await first_result.bounding_box()
                if box:
                    await page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2, steps=10)
                await first_result.click(timeout=5000)
                logger.info("✅ Clicked first search result")
            else:
                logger.info("ℹ️ No results found to click")
        except Exception as e:
            logger.error(f"crawl_state error: {e}")
            raise

    async def close_all(self):
        """Close all active sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# Global instance
stream_manager = BrowserStreamManager()
