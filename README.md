# Intelligent Documentation Navigator

A Hybrid RAG pipeline using a PageIndex approach to solve hierarchical documentation retrieval.

## Architecture
1. **PageIndex**: Parses docs into pages, sections, headings.
2. **Query Routing**: Embeds query, finds top pages.
3. **Hybrid Retrieval**: BM25 + Vector search inside the page.
4. **RAG**: Feeds scoped chunks + metadata to LLM.
