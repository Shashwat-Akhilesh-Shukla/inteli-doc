import os
from typing import List
from whoosh.index import open_dir
from whoosh.qparser import QueryParser, OrGroup
from langchain_core.documents import Document
from backend.utils.logger import get_logger

logger = get_logger()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "whoosh_index")

class SparseRetriever:
    """
    Handles keyword/sparse searches against the Whoosh index.
    """
    def __init__(self):
        if not os.path.exists(INDEX_DIR):
            logger.warning(f"Whoosh index directory {INDEX_DIR} does not exist. Keyword search may fail.")
            self.ix = None
        else:
            self.ix = open_dir(INDEX_DIR)
            
    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Parses query and retrieves top_k documents using BM25 scoring implicitly via Whoosh.
        """
        if not self.ix:
            logger.error("Whoosh index not initialized.")
            return []
            
        logger.info(f"Sparse search triggered for query: '{query}'")
        
        # Use OrGroup so that partial keyword matches are valid
        parsed_query = QueryParser("content", self.ix.schema, group=OrGroup.factory(0.9)).parse(query)
        
        docs = []
        with self.ix.searcher() as searcher:
            results = searcher.search(parsed_query, limit=top_k)
            for hit in results:
                # Include rank and raw score in metadata
                metadata = {
                    "id": hit.get("id"),
                    "source": hit.get("source"),
                    "score": hit.score,
                    "rank": hit.rank
                }
                docs.append(Document(page_content=hit.get("content", ""), metadata=metadata))
        
        logger.info(f"Sparse search returned {len(docs)} documents.")
        return docs
