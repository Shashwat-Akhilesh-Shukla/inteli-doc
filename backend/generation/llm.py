import os
from typing import AsyncGenerator, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.documents import Document

from backend.generation.prompts import SYSTEM_PROMPT_TEMPLATE
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class ResponseGenerator:
    def __init__(self, temperature: float = 0.0):
        model_name = os.getenv("GENERATION_MODEL", "gpt-4o")
        logger.info(f"Initializing ResponseGenerator with model: {model_name} at temp: {temperature}")
        self.llm = ChatOpenAI(model=model_name, temperature=temperature, streaming=True)

    def _format_context(self, documents: List[Document]) -> tuple[str, Dict[str, Any]]:
        """
        Takes retrieved documents and formats them into a single context string
        with [Doc X] identifiers. Also returns the metadata dictionary mapped to those identifiers.
        """
        formatted_context = ""
        context_metadata = {}
        
        for idx, doc in enumerate(documents, start=1):
            doc_id = f"Doc {idx}"
            formatted_context += f"[{doc_id}]\nContent:\n{doc.page_content}\n\n"
            # Accumulate metadata to send back to client
            context_metadata[f"[{doc_id}]"] = doc.metadata

        return formatted_context, context_metadata

    async def generate_stream(self, query: str, documents: List[Document], history: List[Dict[str, str]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Asynchronously yields response tokens and finally yields the context metadata
        for precise UI citations. Yields dictionaries formatted for WebSocket/Streaming outputs.
        Now supports multi-turn conversation.
        """
        logger.info(f"Starting response generation stream for query: '{query}'")
        
        if not documents:
            logger.warning("No documents provided to generator. Yielding static refusal.")
            yield {"type": "token", "content": "I couldn't find any relevant information in the documentation to answer your query."}
            yield {"type": "metadata", "content": {}}
            return
        
        context_text, context_metadata = self._format_context(documents)
        
        system_content = SYSTEM_PROMPT_TEMPLATE.format(context_text=context_text)
        
        # Build message list with history
        messages = [SystemMessage(content=system_content)]
        if history:
            for m in history:
                if m["role"] == "user":
                    messages.append(HumanMessage(content=m["content"]))
                elif m["role"] == "assistant":
                    messages.append(AIMessage(content=m["content"]))
        
        messages.append(HumanMessage(content=query))
        
        # Stream response
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield {"type": "token", "content": chunk.content}
        except Exception as e:
            logger.error(f"Error during streaming generation: {e}")
            yield {"type": "error", "content": str(e)}
            
        # After token stream is complete, emit the gathered metadata
        yield {"type": "metadata", "content": context_metadata}
        logger.info("Finished streaming response and metadata.")
