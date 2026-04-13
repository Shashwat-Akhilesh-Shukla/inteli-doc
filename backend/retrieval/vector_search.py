import os
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document
from backend.utils.logger import get_logger

logger = get_logger()

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "doc_navigator"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class DenseRetriever:
    """
    Handles dense vector searches against the Qdrant database.
    """
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)
        
    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Embeds the query and fetches the top_k most similar documents.
        """
        logger.info(f"Dense search triggered for query: '{query}'")
        
        # Embed query
        query_vector = self.encoder.encode([query])[0]
        
        # Search Qdrant
        search_result = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector.tolist(),
            limit=top_k
        )
        
        docs = []
        for hit in search_result:
            payload = hit.payload or {}
            text = payload.get("text", "")
            # Assume any other payload fields are metadata
            metadata = {k: v for k, v in payload.items() if k != "text"}
            metadata["score"] = hit.score  # Include raw similarity score
            docs.append(Document(page_content=text, metadata=metadata))
            
        logger.info(f"Dense search returned {len(docs)} documents.")
        return docs
