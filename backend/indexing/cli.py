import argparse
from pathlib import Path
from backend.utils.logger import get_logger
from backend.indexing.parsers import parse_document
from backend.indexing.chunking import chunk_documents
from backend.indexing.qdrant_store import DenseIndexer
from backend.indexing.whoosh_store import SparseIndexer

logger = get_logger()

def main():
    parser = argparse.ArgumentParser(description="Ingest documents into Qdrant and Whoosh.")
    parser.add_argument("--dir", type=str, required=True, help="Directory containing documents to parse")
    parser.add_argument("--chunk-size", type=int, default=1000, help="Chunk size limiter")
    parser.add_argument("--chunk-overlap", type=int, default=200, help="Overlap to preserve context boundaries")
    
    args = parser.parse_args()
    
    input_dir = Path(args.dir)
    if not input_dir.exists() or not input_dir.is_dir():
        logger.error(f"Directory {input_dir} does not exist.")
        return
        
    all_chunks = []
    allowed_exts = {".pdf", ".md", ".txt", ".htm", ".html"}
    
    logger.info(f"Scanning {input_dir} for documents...")
    
    for filepath in input_dir.rglob("*"):
        if filepath.is_file() and filepath.suffix.lower() in allowed_exts:
            docs = parse_document(str(filepath))
            logger.info(f"Loaded {len(docs)} logical pages from {filepath.name}")
            
            chunks = chunk_documents(docs, args.chunk_size, args.chunk_overlap)
            all_chunks.extend(chunks)
            
    if not all_chunks:
        logger.warning("No chunks generated. Data was empty. Exiting.")
        return
        
    logger.info(f"Pushing {len(all_chunks)} chunks to Vector & Sparse Stores...")
    
    dense = DenseIndexer()
    dense.index_chunks(all_chunks)
    
    sparse = SparseIndexer()
    sparse.index_chunks(all_chunks)
    
    logger.info("Ingestion pipeline completed gracefully.")

if __name__ == "__main__":
    main()
