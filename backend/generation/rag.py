import json
from typing import AsyncGenerator, Dict, Any

from backend.agents.agentic_loop import AgenticLoop
from backend.generation.llm import ResponseGenerator
from backend.utils.logger import get_logger

logger = get_logger(__name__)

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
        async for payload in self.generator.generate_stream(query=query, documents=retrieved_docs):
            yield json.dumps(payload)
