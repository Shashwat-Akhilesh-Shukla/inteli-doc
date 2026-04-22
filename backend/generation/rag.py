import json
import os
import redis
from typing import AsyncGenerator, Dict, Any, List

from backend.agents.agentic_loop import AgenticLoop
from backend.generation.llm import ResponseGenerator
from backend.utils.logger import get_logger

logger = get_logger(__name__)

redis_host = os.getenv("REDIS_HOST", "localhost")
try:
    redis_client = redis.Redis(host=redis_host, port=6379, db=0, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to initialize Redis client: {e}")
    redis_client = None

class RAGPipeline:
    """
    Coordinates the full flow from user query -> Agentic Routing/Retrieval -> Streaming Generation.
    Now supports multi-turn conversation history.
    """
    def __init__(self, max_retrieval_iterations: int = 3):
        logger.info("Initializing complete RAG Pipeline...")
        self.agentic_loop = AgenticLoop(max_iterations=max_retrieval_iterations)
        self.generator = ResponseGenerator()

    async def aquery_stream(self, query: str, history: List[Dict[str, str]] = None) -> AsyncGenerator[str, None]:
        """
        Executes the pipeline and yields JSON-encoded strings for WebSocket or Server-Sent Events.
        Incorporates history for contextual awareness.
        """
        logger.info(f"RAG Pipeline triggered for query: '{query}' with {len(history or [])} history msgs.")
        
        # Check Redis Cache
        if redis_client:
            try:
                cached_data = redis_client.get(query)
                if cached_data:
                    logger.info("Cache hit! Streaming from Redis...")
                    cached_chunks = json.loads(cached_data)
                    for chunk in cached_chunks:
                        yield chunk
                    return
            except Exception as e:
                logger.error(f"Redis cache read error: {e}")
        
        retrieved_docs = []
        final_route = "docs_search"
        
        try:
            # Consume the agentic loop stream and yield status phases
            async for update in self.agentic_loop.arun_stream(query, history=history):
                if update["type"] == "phase":
                    logger.info(f"Agent Phase: {update['content']}")
                    yield json.dumps({"type": "phase", "content": update["content"]})
                
                # Accumulate the final state (documents and route)
                if update["type"] == "state_update":
                    node_update = update["update"]
                    if "documents" in node_update:
                        retrieved_docs = node_update["documents"]
                    if "route" in node_update:
                        final_route = node_update["route"]
            
            if final_route == "general":
                logger.info("Query routed as 'general'. Bypassing retrieved documents.")
                retrieved_docs = []
                
        except Exception as e:
            logger.error(f"Error during agentic loop execution: {e}")
            yield json.dumps({"type": "error", "content": f"Retrieval error: {str(e)}"})
            return

        # Stream Response via Generator
        cached_chunks_to_save = []
        async for payload in self.generator.generate_stream(query=query, documents=retrieved_docs, history=history):
            chunk_str = json.dumps(payload)
            cached_chunks_to_save.append(chunk_str)
            yield chunk_str

        # Save to Redis Cache
        if redis_client:
            try:
                # Cache for 1 hour (3600 seconds)
                redis_client.setex(query, 3600, json.dumps(cached_chunks_to_save))
            except Exception as e:
                logger.error(f"Redis cache write error: {e}")
