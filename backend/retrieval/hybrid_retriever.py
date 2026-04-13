import hashlib
from typing import List, Dict
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder

from backend.utils.logger import get_logger
from backend.retrieval.vector_search import DenseRetriever
from backend.retrieval.keyword_search import SparseRetriever

logger = get_logger()

# Constants
RRF_K = 60
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

class HybridRetriever:
    """
    Combines Dense and Sparse retrievals utilizing Reciprocal Rank Fusion (RRF),
    and re-ranks the top results using a high-precision Cross-Encoder.
    """
    def __init__(self):
        self.dense_retriever = DenseRetriever()
        self.sparse_retriever = SparseRetriever()
        logger.info(f"Loading Cross-Encoder model '{CROSS_ENCODER_MODEL}' for re-ranking...")
        self.cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
        
    def _hash_content(self, text: str) -> str:
        """Create a reproducible hash for chunk content to merge hits from different DBs."""
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Executes hybrid search fetching candidates from dense & sparse indices,
        merges them via RRF, and re-ranks via Cross-Encoder.
        """
        logger.info(f"Hybrid search triggered for query: '{query}'")
        
        # Increase internal fetch limit to ensure diverse candidate pool before re-ranking
        fetch_k = max(top_k * 2, 10)
        
        dense_docs = self.dense_retriever.search(query, top_k=fetch_k)
        sparse_docs = self.sparse_retriever.search(query, top_k=fetch_k)
        
        # Merge via Reciprocal Rank Fusion
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Document] = {}
        
        def process_docs(docs: List[Document], weight: float = 1.0):
            for rank, doc in enumerate(docs):
                doc_hash = self._hash_content(doc.page_content)
                if doc_hash not in rrf_scores:
                    rrf_scores[doc_hash] = 0.0
                    doc_map[doc_hash] = doc
                    
                # RRF Formula
                rrf_scores[doc_hash] += weight * (1.0 / (RRF_K + rank + 1))

        process_docs(dense_docs, weight=1.0)
        process_docs(sparse_docs, weight=1.0) # Equal weighting
        
        # Sort candidates by combined RRF score
        sorted_hashes = sorted(rrf_scores.keys(), key=lambda h: rrf_scores[h], reverse=True)
        top_candidates = [doc_map[h] for h in sorted_hashes[:fetch_k]]
        
        if not top_candidates:
            return []
            
        # Cross-Encoder Re-ranking
        logger.info(f"Re-ranking {len(top_candidates)} candidates via Cross-Encoder...")
        pairs = [[query, doc.page_content] for doc in top_candidates]
        ce_scores = self.cross_encoder.predict(pairs)
        
        # Attach cross-encoder scores
        for doc, ce_score in zip(top_candidates, ce_scores):
            doc.metadata["cross_encoder_score"] = float(ce_score)
            
        # Sort by actual cross-encoder semantic score
        reranked_docs = sorted(top_candidates, key=lambda d: d.metadata["cross_encoder_score"], reverse=True)
        
        final_docs = reranked_docs[:top_k]
        logger.info(f"Hybrid search successfully mapped {len(final_docs)} final documents.")
        
        return final_docs
