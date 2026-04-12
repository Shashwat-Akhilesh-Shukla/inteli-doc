import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer
from langchain_core.documents import Document
from typing import List
from backend.utils.logger import get_logger

logger = get_logger()

# Connection to the docker-composed Qdrant instance
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION_NAME = "doc_navigator"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

class DenseIndexer:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        self.encoder = SentenceTransformer(EMBEDDING_MODEL)
        self.vector_size = self.encoder.get_sentence_embedding_dimension()
        self._ensure_collection()
        
    def _ensure_collection(self):
        if not self.client.collection_exists(COLLECTION_NAME):
            self.client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
            
    def index_chunks(self, chunks: List[Document]):
        if not chunks:
            return
            
        texts = [doc.page_content for doc in chunks]
        metadatas = [doc.metadata for doc in chunks]
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = self.encoder.encode(texts, show_progress_bar=False)
        
        points = []
        for embedding, text, metadata in zip(embeddings, texts, metadatas):
            points.append({
                "id": str(uuid.uuid4()),
                "vector": embedding.tolist(),
                "payload": {"text": text, **metadata}
            })
            
        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        logger.info(f"Successfully indexed {len(chunks)} dense vectors in Qdrant.")
