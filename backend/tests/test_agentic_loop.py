import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from backend.agents.agentic_loop import AgenticLoop
from backend.agents.evaluation import EvaluationResult

@patch("backend.agents.agentic_loop.HybridRetriever")
@patch("backend.agents.agentic_loop.QueryRewriter")
@patch("backend.agents.agentic_loop.ContextEvaluator")
@patch("backend.agents.agentic_loop.QueryRouter")
def test_agentic_loop_sufficient_first_try(MockRouter, MockEvaluator, MockRewriter, MockRetriever):
    """Test that the loop ends early if the first retrieval is sufficient."""
    # Setup mocks
    mock_router = MockRouter.return_value
    mock_router.route_query.return_value = "docs_search"
    
    mock_retriever = MockRetriever.return_value
    mock_retriever.search.return_value = [Document(page_content="Here is how to do X.", metadata={"source": "doc1"})]
    
    mock_evaluator = MockEvaluator.return_value
    mock_evaluator.evaluate.return_value = EvaluationResult(status="SUFFICIENT", feedback="Good context.")
    
    # Initialize and run loop
    loop = AgenticLoop(max_iterations=3)
    result = loop.run("How do I do X?")
    
    # Assertions
    assert result["route"] == "docs_search"
    assert len(result["documents"]) == 1
    assert result["iterations"] == 1
    assert result["status"] == "SUFFICIENT"
    assert result["current_query"] == "How do I do X?"
    
    mock_router.route_query.assert_called_once()
    mock_retriever.search.assert_called_once()
    mock_evaluator.evaluate.assert_called_once()
    mock_rewriter = MockRewriter.return_value
    mock_rewriter.rewrite.assert_not_called()

@patch("backend.agents.agentic_loop.HybridRetriever")
@patch("backend.agents.agentic_loop.QueryRewriter")
@patch("backend.agents.agentic_loop.ContextEvaluator")
@patch("backend.agents.agentic_loop.QueryRouter")
def test_agentic_loop_max_iterations_reached(MockRouter, MockEvaluator, MockRewriter, MockRetriever):
    """Test that the loop rewrites and eventually stops if max iterations reached."""
    # Setup mocks
    mock_router = MockRouter.return_value
    mock_router.route_query.return_value = "docs_search"
    
    mock_retriever = MockRetriever.return_value
    mock_retriever.search.return_value = [Document(page_content="Random stuff.", metadata={})]
    
    mock_evaluator = MockEvaluator.return_value
    mock_evaluator.evaluate.return_value = EvaluationResult(status="INSUFFICIENT", feedback="Not what I asked.")
    
    mock_rewriter = MockRewriter.return_value
    mock_rewriter.rewrite.return_value = "Rewritten Query"
    
    # Initialize and run loop with small max_iterations
    max_iter = 2
    loop = AgenticLoop(max_iterations=max_iter)
    result = loop.run("How do I do X?")
    
    # Assertions
    assert result["route"] == "docs_search"
    assert result["iterations"] == max_iter
    assert result["status"] == "INSUFFICIENT"
    assert result["current_query"] == "Rewritten Query"
    
    # Retrieval should be called `max_iter` times
    assert mock_retriever.search.call_count == max_iter
    assert mock_evaluator.evaluate.call_count == max_iter
    assert mock_rewriter.rewrite.call_count == max_iter - 1
