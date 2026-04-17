import json
import os
import redis
from typing import AsyncGenerator, Dict, Any

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
    """
    def __init__(self, max_retrieval_iterations: int = 3):
        logger.info("Initializing complete RAG Pipeline...")
        self.agentic_loop = AgenticLoop(max_iterations=max_retrieval_iterations)
        self.generator = ResponseGenerator()

    async def aquery_stream(self, query: str) -> AsyncGenerator[str, None]:
        """
        Executes the pipeline and yields JSON-encoded strings for WebSocket or Server-Sent Events.
        Each yield represents a chunk of the response.
        """
        logger.info(f"RAG Pipeline triggered for query: '{query}'")
        
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
        
        try:
            agent_state = self.agentic_loop.run(query)
            retrieved_docs = agent_state.get("documents", [])
            route = agent_state.get("route", "docs_search")
            
            if route == "general":
                logger.info("Query routed as 'general'. Bypassing retrieved documents.")
                retrieved_docs = []
                
        except Exception as e:
            logger.error(f"Error during agentic loop execution: {e}")
            yield json.dumps({"type": "error", "content": "Failed to retrieve context."})
            return

        # Stream Response via Generator
        cached_chunks_to_save = []
        async for payload in self.generator.generate_stream(query=query, documents=retrieved_docs):
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
