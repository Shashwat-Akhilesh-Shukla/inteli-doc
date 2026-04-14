import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from langchain_core.documents import Document
from collections import namedtuple

from backend.generation.llm import ResponseGenerator
from backend.generation.rag import RAGPipeline

Chunk = namedtuple("Chunk", ["content"])

@pytest.mark.asyncio
async def test_response_generator_stream():
    docs = [Document(page_content="Test data", metadata={"source": "test.md"})]
    
    async def mock_astream(*args, **kwargs):
        for token in ["Hello", " world", "!"]:
             yield Chunk(content=token)
             
    with patch("backend.generation.llm.ChatOpenAI") as MockLLM:
        mock_llm_instance = MockLLM.return_value
        mock_llm_instance.astream = mock_astream
        
        generator = ResponseGenerator()
        iterator = generator.generate_stream("What is this?", docs)
        
        tokens = []
        metadata = None
        async for payload in iterator:
            if payload["type"] == "token":
                tokens.append(payload["content"])
            elif payload["type"] == "metadata":
                metadata = payload["content"]
                
        assert "".join(tokens) == "Hello world!"
        assert metadata is not None
        assert "[Doc 1]" in metadata
        assert metadata["[Doc 1]"]["source"] == "test.md"

@pytest.mark.asyncio
async def test_rag_pipeline_aquery_stream():
    with patch("backend.generation.rag.AgenticLoop") as MockLoop:
        mock_loop_inst = MockLoop.return_value
        mock_loop_inst.run.return_value = {
            "route": "docs_search",
            "documents": [Document(page_content="Data", metadata={"id": 1})]
        }
        
        with patch("backend.generation.rag.ResponseGenerator") as MockGen:
            mock_gen_inst = MockGen.return_value
            
            async def mock_gen_stream(*args, **kwargs):
                yield {"type": "token", "content": "Success"}
                yield {"type": "metadata", "content": {"[Doc 1]": {"id": 1}}}
                
            mock_gen_inst.generate_stream = mock_gen_stream
            
            pipeline = RAGPipeline()
            stream = pipeline.aquery_stream("Query?")
            
            results = []
            async for json_str in stream:
                results.append(json.loads(json_str))
                
            assert len(results) == 2
            assert results[0]["content"] == "Success"
            assert results[1]["type"] == "metadata"
