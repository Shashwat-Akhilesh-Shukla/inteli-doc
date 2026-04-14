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

    def route_query(self, query: str) -> str:
        """Classifies the given query into a specific route."""
        logger.info(f"Routing query: {query}")
        result = self.structured_llm.invoke(
            f"Classify the following user query. If it is a generic greeting "
            f"or small talk, classify as 'general'. If it looks like a request for "
            f"help debugging an error, classify as 'troubleshoot'. Otherwise, and for all "
            f"other technical questions, classify as 'docs_search'. Query: '{query}'"
        )
        logger.info(f"Query classified as route: {result.route}")
        return result.route
