# Agentic Loop: Query Rewriting

from pydantic import BaseModel, Field
from backend.agents.llm_dependencies import get_reasoning_llm
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class RewriteResult(BaseModel):
    """The rewritten query."""
    rewritten_query: str = Field(
        description="The optimized resulting query to use for the next search iteration."
    )

class QueryRewriter:
    def __init__(self):
        self.llm = get_reasoning_llm()
        self.structured_llm = self.llm.with_structured_output(RewriteResult)

    def rewrite(self, original_query: str, current_query: str, feedback: str) -> str:
        """Rewrites the query based on the feedback from the evaluation."""
        logger.info(f"Rewriting query: {current_query}")
        prompt = (
            f"You are a helpful assistant assisting in a doc search flow. "
            f"The original query was: '{original_query}'.\n"
            f"The previous search query we tried was: '{current_query}'.\n"
            f"The evaluator provided the following reason for why the search failed or was insufficient: '{feedback}'.\n"
            f"Please rewrite the query to be more effective for a semantic and keyword search engine. "
            f"Try broadening the search terms, omitting too-specific jargon if it failed to match, "
            f"or using synonyms that might appear in the documentation."
        )
        result: RewriteResult = self.structured_llm.invoke(prompt)
        logger.info(f"Query rewritten to: {result.rewritten_query}")
        return result.rewritten_query
