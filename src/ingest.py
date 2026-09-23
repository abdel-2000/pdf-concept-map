import sys
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from database import get_connection

model = SentenceTransformer("all-MiniLM-L6-v2")

def extract_text_by_page(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if text.strip():
            pages.append((i + 1, text))
    return pages

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap
    return chunks

def ingest_pdf(pdf_path, source_name=None):
    source_name = source_name or pdf_path
    pages = extract_text_by_page(pdf_path)
    conn = get_connection()
    cur = conn.cursor()

    total_chunks = 0
    for page_num, text in pages:
        for chunk in chunk_text(text):
            embedding = model.encode(chunk)
            cur.execute(
                "INSERT INTO documents (source, page, content, embedding) VALUES (%s, %s, %s, %s)",
                (source_name, page_num, chunk, embedding),
            )
            total_chunks += 1

    conn.commit()
    cur.close()
    conn.close()
    print(f"Ingested {total_chunks} chunks from {source_name}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_pdf>")
        sys.exit(1)
    ingest_pdf(sys.argv[1])