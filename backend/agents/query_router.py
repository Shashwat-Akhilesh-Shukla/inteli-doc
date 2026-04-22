from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from backend.agents.llm_dependencies import get_reasoning_llm
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class RouteClassification(BaseModel):
    """Classification of the user query to decide the next step."""
    route: str = Field(
        description="The category of the route. Must be one of: 'general', 'docs_search', 'troubleshoot'."
    )

class QueryRouter:
    def __init__(self):
        self.llm = get_reasoning_llm()
        self.structured_llm = self.llm.with_structured_output(RouteClassification)

    def route_query(self, query: str, history: List[Dict[str, str]] = None) -> str:
        """
        Classifies the given query into a specific route, 
        considering conversation history for context.
        """
        logger.info(f"Routing query: {query}")
        
        history_context = ""
        if history:
            history_context = "Conversation history for context:\n" + \
                "\n".join([f"{m['role']}: {m['content']}" for m in history[-3:]]) + "\n\n"

        prompt = (
            f"{history_context}"
            f"Classify the following current user query. If it is a generic greeting "
            f"or small talk, classify as 'general'. If it looks like a request for "
            f"help debugging an error, classify as 'troubleshoot'. Otherwise, and for all "
            f"other technical questions, classify as 'docs_search'.\n\n"
            f"Current Query: '{query}'"
        )
        
        result = self.structured_llm.invoke(prompt)
        logger.info(f"Query classified as route: {result.route}")
        return result.route
