from pydantic import BaseModel, Field
from backend.agents.llm_dependencies import get_reasoning_llm
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class EvaluationResult(BaseModel):
    """The result of evaluating retrieved context against the query."""
    status: str = Field(
        description="Must be 'SUFFICIENT' if the context contains enough information to answer the query, otherwise 'INSUFFICIENT'."
    )
    feedback: str = Field(
        description="A brief explanation of why it is sufficient or what is missing if insufficient."
    )

class ContextEvaluator:
    def __init__(self):
        self.llm = get_reasoning_llm()
        self.structured_llm = self.llm.with_structured_output(EvaluationResult)

    def evaluate(self, query: str, context: str) -> EvaluationResult:
        """Evaluates whether the given context is sufficient to answer the query."""
        logger.info(f"Evaluating context for query: {query}")
        
        if not context or not context.strip():
            logger.info("Context is empty. Returning INSUFFICIENT.")
            return EvaluationResult(status="INSUFFICIENT", feedback="No context was retrieved.")
            
        prompt = (
            f"You are evaluating if retrieved documentation context can answer a user query.\n"
            f"User Query:\n{query}\n\n"
            f"Retrieved Context:\n{context}\n\n"
            f"Determine if the Context provides enough details to accurately and completely answer the Query. "
            f"Return 'SUFFICIENT' if yes, or 'INSUFFICIENT' if entirely missing or partial. "
            f"Also, provide brief feedback."
        )
        result: EvaluationResult = self.structured_llm.invoke(prompt)
        logger.info(f"Evaluation resulted in status: {result.status}")
        return result
