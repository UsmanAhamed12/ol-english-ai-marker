"""Retrieval-augmented generation, all of it local.

    llm.py          the Ollama client: OCR, text and JSON answers
    embeddings.py   the embedding model and the Chroma client
    vectorstore.py  dense index (LlamaIndex + Chroma)
    retriever.py    the knowledge base: chunking, indexing, search
    splitter.py     how a document is cut into chunks
    loaders.py      a PDF or photo -> page images -> text
    chains.py       the two prompt chains the marker runs
    prompts/        every prompt template, in one folder
"""