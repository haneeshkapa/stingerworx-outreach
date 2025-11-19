from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
import logging
from aiortc import RTCSessionDescription
import uuid
import threading

from database import get_db
from models import Dealer
from auth import get_current_tenant_id
from webrtc_streaming import stream_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["webrtc"]
)

@router.post("/demo-browser")
def demo_visible_browser(
    dealer_name: str = "5 SHOT FIREARMS",
    db: Session = Depends(get_db),
    tenant_id: int = Depends(get_current_tenant_id)
):
    """
    Run browser automation in VISIBLE mode (non-headless) for demonstration.
    Open VNC viewer to watch it live!
    """
    from scrapers.crawl4ai_search import run_async_search
    
    # Find the dealer in the database
    dealer = db.query(Dealer).filter(
        Dealer.tenant_id == tenant_id,
        Dealer.business_name.ilike(f"%{dealer_name}%")
    ).first()
    
    if not dealer:
        return {"error": f"Dealer '{dealer_name}' not found"}
    
    # Run browser automation in background thread so API responds immediately
    def run_browser_demo():
        try:
            print(f"\n🎬 Starting visible browser demo for {dealer.business_name}...")
            result = run_async_search(
                dealer.business_name,
                dealer.city,
                dealer.state,
                headless=False  # VISIBLE BROWSER!
            )
            print(f"✅ Browser demo completed! Found: {result.get('url') if result else 'Nothing'}")
        except Exception as e:
            print(f"❌ Browser demo error: {str(e)}")
    
    # Start background thread
    thread = threading.Thread(target=run_browser_demo, daemon=True)
    thread.start()
    
    return {
        "message": f"🎬 Browser demo started for {dealer.business_name}!",
        "dealer": dealer.business_name,
        "status": "running",
        "note": "The VNC viewer should appear automatically in your Replit workspace. Watch the browser navigate in real-time! Check the Logs page to see progress."
    }

@router.post("/webrtc/offer")
async def webrtc_offer(request: dict):
    """
    WebRTC signaling endpoint - receives offer from client, returns answer.
    Creates new browser streaming session and sets up peer connection.
    """
    try:
        # Parse offer
        offer = RTCSessionDescription(sdp=request["sdp"], type=request["type"])
        session_id = str(uuid.uuid4())
        
        logger.info(f"📡 Received WebRTC offer for session {session_id}")
        
        # Create new streaming session (test pattern)
        pc = await stream_manager.create_session(session_id)
        
        # Set remote description (offer)
        await pc.setRemoteDescription(offer)
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        logger.info(f"✅ WebRTC answer created for session {session_id}")
        
        return {
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"❌ WebRTC offer error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webrtc/navigate/{session_id}")
async def webrtc_navigate(session_id: str, request: dict):
    """Navigate browser in WebRTC session"""
    try:
        url = request.get("url")
        if url:
            await stream_manager.navigate_session(session_id, url)
            return {"status": "navigated", "url": url}
        else:
            raise HTTPException(status_code=400, detail="URL required")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webrtc/search/{session_id}")
async def webrtc_search(session_id: str, request: dict):
    """Perform Google search in WebRTC session"""
    try:
        query = request.get("query")
        if query:
            await stream_manager.search_session(session_id, query)
            return {"status": "searching", "query": query}
        else:
            raise HTTPException(status_code=400, detail="Query required")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webrtc/crawl/{session_id}")
async def webrtc_crawl(session_id: str, request: dict):
    """Perform a deeper visible crawl for a state (moves mouse, clicks first result)"""
    try:
        state = request.get("state")
        if not state:
            raise HTTPException(status_code=400, detail="State required")
        await stream_manager.crawl_state(session_id, state)
        return {"status": "crawling", "state": state}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"crawl error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/webrtc/session/{session_id}")
async def webrtc_close_session(session_id: str):
    """Close WebRTC streaming session"""
    try:
        await stream_manager.close_session(session_id)
        return {"status": "closed", "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
