CREATE EXTENSION IF NOT EXISTS vector
ALTER TABLE document_chunks ADD COLUMN embedding vector(1536)
CREATE INDEX idx_document_chunks_embedding_cosine ON document_chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)