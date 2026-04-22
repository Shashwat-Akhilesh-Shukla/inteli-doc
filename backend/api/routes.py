from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from backend.api.schemas import ChatRequest, ErrorResponse
from backend.generation.rag import RAGPipeline
from backend.utils.logger import get_logger

logger = get_logger(__name__)

api_router = APIRouter(prefix="/v1")
ws_router = APIRouter(prefix="/ws/v1")

# Single instance for the app lifecycle
rag_pipeline = RAGPipeline(max_retrieval_iterations=3)

@api_router.get("/health", summary="Health Check")
async def health_check():
    """Returns the operational status of the backend API."""
    return {"status": "ok", "service": "Intelligent Doc API"}

@ws_router.websocket("/chat_stream")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time token streaming.
    Receives simple text queries and returns structured JSON responses.
    """
    await websocket.accept()
    logger.info("WebSocket connection established.")
    
    try:
        while True:
            # Wait for client to send a query JSON: { "query": "...", "history": [...] }
            data = await websocket.receive_json()
            query = data.get("query")
            history = data.get("history", [])
            
            logger.info(f"WS received query: {query} with {len(history)} history messages.")
            
            # Start streaming the RAG LLM pipeline tokens
            async for chunk in rag_pipeline.aquery_stream(query, history=history):
                await websocket.send_text(chunk)
                
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected gracefully.")
    except Exception as e:
        logger.error(f"WebSocket execution error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal Error")
        except:
            pass
