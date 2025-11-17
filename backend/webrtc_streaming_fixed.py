"""
WebRTC Browser Streaming - Fixed for Replit/gVisor
Launches Chromium as external process, connects via CDP
"""
import asyncio
import logging
import subprocess
from typing import Optional
import numpy as np
from PIL import Image
import io

from playwright.async_api import async_playwright, Page, Browser
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame

logger = logging.getLogger(__name__)

class ChromiumManager:
    """Manages external Chromium process for Replit environment"""
    
    def __init__(self, port: int = 9222):
        self.port = port
        self.process: Optional[subprocess.Popen] = None
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        
    async def start(self):
        """Launch Chromium as separate process and connect via CDP"""
        logger.info(f"🚀 Launching external Chromium on port {self.port}")
        
        # Launch Chromium with proper flags for Replit
        chromium_cmd = [
            'chromium',
            '--headless=new',
            '--single-process',
            f'--remote-debugging-port={self.port}',
            '--no-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--disable-setuid-sandbox',
            'about:blank'
        ]
        
        self.process = subprocess.Popen(
            chromium_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for debugging port to be ready
        await asyncio.sleep(2)
        
        # Connect Playwright to running Chromium
        logger.info(f"🔌 Connecting Playwright to Chromium via CDP")
        self.playwright = await async_playwright().start()
        
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(
                f'http://localhost:{self.port}'
            )
            logger.info("✅ Connected to Chromium!")
            
            # Get default context and page
            contexts = self.browser.contexts
            if contexts:
                context = contexts[0]
                pages = context.pages
                if pages:
                    self.page = pages[0]
                else:
                    self.page = await context.new_page()
            else:
                context = await self.browser.new_context(
                    viewport={'width': 1280, 'height': 720}
                )
                self.page = await context.new_page()
            
            await self.page.set_viewport_size({'width': 1280, 'height': 720})
            logger.info("✅ Browser ready for streaming!")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Chromium: {e}")
            if self.process:
                self.process.kill()
            raise
    
    async def navigate(self, url: str):
        """Navigate to URL"""
        if self.page:
            try:
                await asyncio.wait_for(
                    self.page.goto(url, wait_until="domcontentloaded"),
                    timeout=10.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Navigation timeout for {url}")
    
    async def screenshot(self) -> Optional[bytes]:
        """Capture screenshot"""
        if self.page:
            try:
                return await asyncio.wait_for(
                    self.page.screenshot(type='jpeg', quality=75),
                    timeout=2.0
                )
            except Exception as e:
                logger.error(f"Screenshot error: {e}")
                return None
        return None
    
    async def stop(self):
        """Stop browser and process"""
        if self.page:
            try:
                await self.page.close()
            except:
                pass
        
        if self.browser:
            try:
                await self.browser.close()
            except:
                pass
        
        if self.playwright:
            try:
                await self.playwright.stop()
            except:
                pass
        
        if self.process:
            self.process.kill()
            self.process.wait()
        
        logger.info("🛑 Chromium stopped")


class BrowserVideoStreamTrack(VideoStreamTrack):
    """aiortc VideoStreamTrack for browser frames"""
    
    def __init__(self, chromium: ChromiumManager):
        super().__init__()
        self.chromium = chromium
        self.placeholder_frame = None
        
    def _create_placeholder(self):
        """Black placeholder frame"""
        img_array = np.zeros((720, 1280, 3), dtype=np.uint8)
        return VideoFrame.from_ndarray(img_array, format='bgr24')
        
    async def recv(self):
        """Get next video frame"""
        pts, time_base = await self.next_timestamp()
        
        try:
            frame_bytes = await self.chromium.screenshot()
            
            if not frame_bytes:
                if not self.placeholder_frame:
                    self.placeholder_frame = self._create_placeholder()
                frame = self.placeholder_frame
            else:
                image = Image.open(io.BytesIO(frame_bytes))
                img_array = np.array(image)
                
                if len(img_array.shape) == 3 and img_array.shape[2] == 3:
                    img_array = img_array[:, :, ::-1]
                
                frame = VideoFrame.from_ndarray(img_array, format='bgr24')
            
            frame.pts = pts
            frame.time_base = time_base
            return frame
            
        except Exception as e:
            logger.error(f"Frame error: {e}")
            if not self.placeholder_frame:
                self.placeholder_frame = self._create_placeholder()
            frame = self.placeholder_frame
            frame.pts = pts
            frame.time_base = time_base
            return frame


class FixedStreamManager:
    """Stream manager using external Chromium"""
    
    def __init__(self):
        self.sessions = {}
        self.port_counter = 9222
        
    async def create_session(self, session_id: str) -> RTCPeerConnection:
        """Create WebRTC session with real browser"""
        logger.info(f"🎥 Creating browser stream session: {session_id}")
        
        # Use unique port for each session
        port = self.port_counter
        self.port_counter += 1
        
        # Start Chromium
        chromium = ChromiumManager(port=port)
        await chromium.start()
        await chromium.navigate("https://www.google.com")
        
        # Create WebRTC peer connection
        pc = RTCPeerConnection()
        
        # Add video track
        video_track = BrowserVideoStreamTrack(chromium)
        pc.addTrack(video_track)
        
        # Store session
        self.sessions[session_id] = {
            'pc': pc,
            'chromium': chromium,
            'track': video_track
        }
        
        # Setup cleanup
        @pc.on("connectionstatechange")
        async def on_state_change():
            logger.info(f"WebRTC state: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.close_session(session_id)
        
        return pc
    
    async def navigate_session(self, session_id: str, url: str):
        """Navigate browser"""
        session = self.sessions.get(session_id)
        if session:
            await session['chromium'].navigate(url)
    
    async def search_session(self, session_id: str, query: str):
        """Perform Google search"""
        session = self.sessions.get(session_id)
        if session and session['chromium'].page:
            await session['chromium'].navigate("https://www.google.com")
            await asyncio.sleep(1)
            try:
                await session['chromium'].page.fill('textarea[name="q"]', query, timeout=5000)
                await session['chromium'].page.press('textarea[name="q"]', 'Enter')
            except Exception as e:
                logger.error(f"Search error: {e}")
    
    async def close_session(self, session_id: str):
        """Close session"""
        session = self.sessions.get(session_id)
        if session:
            await session['chromium'].stop()
            await session['pc'].close()
            del self.sessions[session_id]
            logger.info(f"🗑️ Closed session: {session_id}")
    
    async def close_all(self):
        """Close all sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# Global instance
fixed_stream_manager = FixedStreamManager()
