import pytest
from langchain_core.documents import Document

from backend.retrieval.vector_search import DenseRetriever
from backend.retrieval.keyword_search import SparseRetriever
from backend.retrieval.hybrid_retriever import HybridRetriever

@pytest.fixture(scope="module")
def sample_query():
    # Make sure this has a chance of returning *some* real chunk 
    # depending on what was ingested (we use a generic term)
    return "What is the system architecture?"

def test_dense_retrieval(sample_query):
    retriever = DenseRetriever()
    docs = retriever.search(sample_query, top_k=2)
    assert isinstance(docs, list)
    if docs:
        assert isinstance(docs[0], Document)
        assert "score" in docs[0].metadata

def test_sparse_retrieval(sample_query):
    retriever = SparseRetriever()
    # It gracefully yields [] if index uninitialized/missing
    docs = retriever.search(sample_query, top_k=2)
    assert isinstance(docs, list)
    if docs:
        assert isinstance(docs[0], Document)
        assert "score" in docs[0].metadata
        assert "rank" in docs[0].metadata

def test_hybrid_retrieval(sample_query):
    retriever = HybridRetriever()
    docs = retriever.search(sample_query, top_k=2)
    assert isinstance(docs, list)
    if docs:
        assert isinstance(docs[0], Document)
        assert "cross_encoder_score" in docs[0].metadata
