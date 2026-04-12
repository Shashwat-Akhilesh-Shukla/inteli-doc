import os
import uuid
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID
from langchain_core.documents import Document
from typing import List
from backend.utils.logger import get_logger

logger = get_logger()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "whoosh_index")

class SparseIndexer:
    def __init__(self):
        self.schema = Schema(id=ID(unique=True, stored=True), 
                             content=TEXT(stored=True), 
                             source=ID(stored=True))
        if not os.path.exists(INDEX_DIR):
            os.makedirs(INDEX_DIR)
            self.ix = create_in(INDEX_DIR, self.schema)
            logger.info("Created new Whoosh index directory.")
        else:
            self.ix = open_dir(INDEX_DIR)
            
    def index_chunks(self, chunks: List[Document]):
        if not chunks:
            return
            
        writer = self.ix.writer()
        for doc in chunks:
            writer.add_document(
                id=str(uuid.uuid4()),
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown")
            )
        writer.commit()
        logger.info(f"Successfully indexed {len(chunks)} sparse documents in Whoosh.")
