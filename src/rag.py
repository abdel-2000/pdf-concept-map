import os
import requests
from sentence_transformers import SentenceTransformer
from database import get_connection

model = SentenceTransformer("all-MiniLM-L6-v2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def retrieve_chunks(question, top_k=5):
    embedding = model.encode(question)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT content, source, page
        FROM documents
        ORDER BY embedding <-> %s
        LIMIT %s;
        """,
        (embedding, top_k),
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def build_prompt(question, chunks):
    context = "\n\n".join(f"[{src}, pagina {page}]\n{content}" for content, src, page in chunks)
    return f"""Rispondi alla domanda usando SOLO le informazioni nel contesto seguente.
Se la risposta non è nel contesto, dì che non lo sai.

CONTESTO:
{context}

DOMANDA: {question}

RISPOSTA:"""

def ask_ollama(prompt):
    r = requests.post(f"{OLLAMA_URL}/api/generate",
                       json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False})
    r.raise_for_status()
    return r.json()["response"]

def answer_question(question, top_k=5):
    chunks = retrieve_chunks(question, top_k)
    if not chunks:
        return "Nessun documento trovato. Carica prima un PDF.", []
    answer = ask_ollama(build_prompt(question, chunks))
    sources = sorted({f"{src} (pagina {page})" for _, src, page in chunks})
    return answer, sources