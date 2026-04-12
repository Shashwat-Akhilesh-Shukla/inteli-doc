from typing import List
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader, BSHTMLLoader, TextLoader
from langchain_core.documents import Document
from backend.utils.logger import get_logger

logger = get_logger()

def parse_document(file_path: str) -> List[Document]:
    """Parse various document types into LangChain Documents."""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return []
        
    ext = path.suffix.lower()
    
    try:
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
            return loader.load()
        elif ext in [".htm", ".html"]:
            loader = BSHTMLLoader(file_path)
            return loader.load()
        elif ext in [".md", ".txt"]:
            loader = TextLoader(file_path, encoding='utf-8')
            return loader.load()
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return []
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        return []
