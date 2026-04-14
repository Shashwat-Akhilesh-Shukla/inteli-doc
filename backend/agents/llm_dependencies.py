import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from backend.utils.logger import get_logger

logger = get_logger(__name__)
load_dotenv()

def get_reasoning_llm(temperature: float = 0.0) -> ChatOpenAI:
    """
    Returns the core reasoning LLM to be used for routing, evaluating, and rewriting.
    Uses ChatOpenAI by default, extracting OPENAI_API_KEY from environment variables.
    """
    # Using a fast, reasoning-capable model
    model_name = os.getenv("REASONING_MODEL", "gpt-4o-mini")
    logger.debug(f"Initializing reasoning LLM with model: {model_name} at temp: {temperature}")
    return ChatOpenAI(model=model_name, temperature=temperature)
