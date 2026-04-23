from typing import TypedDict, List, Optional, Any, AsyncGenerator, Dict
from langgraph.graph import StateGraph, END
from langchain_core.documents import Document

from backend.agents.query_router import QueryRouter
from backend.agents.evaluation import ContextEvaluator
from backend.agents.rewriter import QueryRewriter
from backend.retrieval.hybrid_retriever import HybridRetriever
from backend.utils.logger import get_logger

logger = get_logger(__name__)

class AgentState(TypedDict):
    original_query: str
    current_query: str
    route: Optional[str]
    documents: List[Document]
    feedback: Optional[str]
    status: Optional[str]
    iterations: int
    history: List[Dict[str, str]]

class AgenticLoop:
    """
    Orchestrates the agentic reasoning loop using LangGraph.
    
    This class defines a state machine that routes queries, retrieves documents,
    evaluates context sufficiency, and rewrites queries if necessary.
    """
    def __init__(self, max_iterations: int = 3):
        """
        Initializes the AgenticLoop with a set of processing nodes and edges.
        
        Args:
            max_iterations (int): The maximum number of times the loop can retry retrieval.
        """
        self.max_iterations = max_iterations
        self.router = QueryRouter()
        self.evaluator = ContextEvaluator()
        self.rewriter = QueryRewriter()
        self.retriever = HybridRetriever()
        
        workflow = StateGraph(AgentState)
        
        # Add processing nodes
        workflow.add_node("route_query", self.route_node)
        workflow.add_node("retrieve_docs", self.retrieve_node)
        workflow.add_node("evaluate_docs", self.evaluate_node)
        workflow.add_node("rewrite_query", self.rewrite_node)
        
        workflow.set_entry_point("route_query")
        
        # Define conditional routing
        workflow.add_conditional_edges(
            "route_query",
            self.route_condition,
            {
                "general": END,
                "docs_search": "retrieve_docs",
                "troubleshoot": "retrieve_docs"
            }
        )
        
        workflow.add_edge("retrieve_docs", "evaluate_docs")
        
        # Define evaluation outcomes
        workflow.add_conditional_edges(
            "evaluate_docs",
            self.evaluate_condition,
            {
                "sufficient": END,
                "rewrite": "rewrite_query",
                "max_iterations_reached": END
            }
        )
        
        workflow.add_edge("rewrite_query", "retrieve_docs")
        
        self.app = workflow.compile()

    def route_node(self, state: AgentState) -> dict:
        """
        Classifies the incoming query to determine the workflow path.
        """
        route = self.router.route_query(state["current_query"], history=state.get("history", []))
        return {"route": route}
        
    def route_condition(self, state: AgentState) -> str:
        """
        Logic for the conditional edge following the route_query node.
        """
        return state.get("route", "docs_search")

    def retrieve_node(self, state: AgentState) -> dict:
        """
        Executes the hybrid search pipeline to fetch relevant document chunks.
        """
        docs = self.retriever.search(state["current_query"], top_k=5)
        return {"documents": docs}
        
    def evaluate_node(self, state: AgentState) -> dict:
        """
        Evaluates whether the retrieved documents provide enough context to answer the query.
        """
        context_text = "\n\n".join([d.page_content for d in state.get("documents", [])])
        eval_result = self.evaluator.evaluate(state["current_query"], context_text)
        return {"feedback": eval_result.feedback, "status": eval_result.status}
        
    def evaluate_condition(self, state: AgentState) -> str:
        """
        Logic for the conditional edge following the evaluate_docs node.
        """
        status = state.get("status", "INSUFFICIENT")
        iterations = state.get("iterations", 1)
        
        if status == "SUFFICIENT":
            logger.info("Context evaluated as SUFFICIENT. Ending retrieval loop.")
            return "sufficient"
            
        if iterations >= self.max_iterations:
            logger.warning(f"Max iterations ({self.max_iterations}) reached. Ending loop with current context.")
            return "max_iterations_reached"
            
        logger.info("Context INSUFFICIENT. Routing to rewrite_query.")
        return "rewrite"
        
    def rewrite_node(self, state: AgentState) -> dict:
        """
        Uses an LLM to hallucinate better search terms based on past failures.
        """
        new_query = self.rewriter.rewrite(
            original_query=state["original_query"],
            current_query=state["current_query"],
            feedback=state.get("feedback", "No feedback provided")
        )
        return {
            "current_query": new_query,
            "iterations": state["iterations"] + 1
        }
        
    async def arun_stream(self, query: str, history: List[Dict[str, str]] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Executes the agentic loop asynchronously, yielding state updates after each node.
        Now preserves and utilizes conversation history.
        """
        initial_state = {
            "original_query": query,
            "current_query": query,
            "route": None,
            "documents": [],
            "feedback": None,
            "status": None,
            "iterations": 1,
            "history": history or []
        }
        
        # Human-readable mapping of LangGraph nodes to UI phases
        node_to_phase = {
            "route_query": "routing",
            "retrieve_docs": "retrieving",
            "evaluate_docs": "evaluating",
            "rewrite_query": "rewriting"
        }

        async for event in self.app.astream(
            initial_state, 
            {"recursion_limit": self.max_iterations * 3 + 2},
            stream_mode="updates"
        ):
            # 'event' is a dict: {node_name: {state_updates}}
            for node_name, state_update in event.items():
                phase = node_to_phase.get(node_name)
                if phase:
                    yield {"type": "phase", "content": phase}
                
                # If we have the final state or transition updates, we yield them
                yield {"type": "state_update", "node": node_name, "update": state_update}
