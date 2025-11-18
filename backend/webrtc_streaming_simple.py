"""
Simple WebRTC streaming with test pattern frames
This bypasses browser complexity to verify the WebRTC pipeline works
"""
import asyncio
import logging
from typing import Optional
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import io
import time

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
ICE_SERVERS = RTCConfiguration(
    iceServers=[
        RTCIceServer(
            urls=[
                "turn:openrelay.metered.ca:80?transport=tcp",
                "turn:openrelay.metered.ca:443?transport=tcp",
            ],
            username="openrelayproject",
            credential="openrelayproject",
        ),
    ],
    iceTransportPolicy="relay",
)

class TestFrameProducer:
    """Generates test pattern frames"""
    
    def __init__(self, target_fps: int = 10):
        self.target_fps = target_fps
        self.frame_counter = 0
        self.start_time = time.time()
        
    def generate_test_frame(self) -> bytes:
        """Generate a test pattern frame with timestamp"""
        # Create image with test pattern
        img = Image.new('RGB', (1280, 720), color=(30, 30, 50))
        draw = ImageDraw.Draw(img)
        
        # Draw grid pattern
        for x in range(0, 1280, 100):
            draw.line([(x, 0), (x, 720)], fill=(60, 60, 80), width=1)
        for y in range(0, 720, 100):
            draw.line([(0, y), (1280, y)], fill=(60, 60, 80), width=1)
        
        # Draw circle that animates
        elapsed = time.time() - self.start_time
        x = int(640 + 300 * np.sin(elapsed))
        y = int(360 + 150 * np.cos(elapsed * 1.5))
        draw.ellipse([x-50, y-50, x+50, y+50], fill=(0, 200, 100))
        
        # Draw text
        text = f"WebRTC Test Stream\nFrame: {self.frame_counter}\nFPS: {self.target_fps}"
        draw.text((50, 50), text, fill=(255, 255, 255))
        
        # Draw "CLICK START STREAM" message
        draw.text((400, 300), "WebRTC Stream Active!", fill=(0, 255, 0), font=None)
        draw.text((450, 350), f"Time: {elapsed:.1f}s", fill=(200, 200, 200))
        
        self.frame_counter += 1
        
        # Convert to JPEG bytes
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    async def get_latest_frame(self) -> Optional[bytes]:
        """Get a fresh frame"""
        return self.generate_test_frame()


class SimpleVideoStreamTrack(VideoStreamTrack):
    """aiortc VideoStreamTrack that streams test pattern frames"""
    
    def __init__(self, frame_producer: TestFrameProducer):
        super().__init__()
        self.frame_producer = frame_producer
        self.counter = 0
        
    async def recv(self):
        """Called by aiortc to get next video frame"""
        pts, time_base = await self.next_timestamp()
        
        try:
            frame_bytes = await self.frame_producer.get_latest_frame()
            
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
            raise


class SimpleStreamManager:
    """Simple stream manager for testing"""
    
    def __init__(self):
        self.sessions = {}
        
    async def create_session(self, session_id: str) -> RTCPeerConnection:
        """Create WebRTC session with test pattern stream"""
        logger.info(f"🎥 Creating test stream session: {session_id}")
        
        # Create test frame producer
        frame_producer = TestFrameProducer(target_fps=15)
        
        # Create WebRTC peer connection
        pc = RTCPeerConnection(ICE_SERVERS)
        
        # Add video track
        video_track = SimpleVideoStreamTrack(frame_producer)
        pc.addTrack(video_track)
        
        # Store session
        self.sessions[session_id] = {
            'pc': pc,
            'producer': frame_producer,
            'track': video_track
        }
        
        # Setup cleanup
        @pc.on("connectionstatechange")
        async def on_state_change():
            logger.info(f"WebRTC state: {pc.connectionState}")
            if pc.connectionState == "failed" or pc.connectionState == "closed":
                await self.close_session(session_id)
        
        logger.info(f"✅ Test stream session created")
        return pc
    
    async def close_session(self, session_id: str):
        """Close session"""
        session = self.sessions.get(session_id)
        if session:
            await session['pc'].close()
            if session_id in self.sessions:
                del self.sessions[session_id]
            logger.info(f"🗑️ Closed session: {session_id}")

    async def navigate_session(self, session_id: str, url: str):
        """Placeholder to keep API compatible with browser-based streamer"""
        logger.info(f"🧭 navigate_session called for {session_id} -> {url} (no-op in test streamer)")

    async def search_session(self, session_id: str, query: str):
        """Placeholder to keep API compatible with browser-based streamer"""
        logger.info(f"🔍 search_session called for {session_id} -> {query} (no-op in test streamer)")

    async def close_all(self):
        """Close all sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)


# Global instance
simple_stream_manager = SimpleStreamManager()
