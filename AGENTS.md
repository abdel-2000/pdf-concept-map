# Architecture

## Pipeline

```
PDF file
   │
   ▼
pdf_extractor.py   → extracts text, detects language, truncates to max_chars
   │
   ▼
llm_mapper.py      → sends text to Ollama, parses JSON concept map
   │
   ▼
graph_renderer.py  → renders NetworkX graph as PNG
   │
   ▼
app.py (Gradio)    → displays image + JSON in the browser
```

## Modules

| File | Role |
|---|---|
| `src/pdf_extractor.py` | PDF → clean text + language detection |
| `src/llm_mapper.py` | text → Ollama → JSON concept map |
| `src/graph_renderer.py` | JSON → NetworkX → PNG |
| `src/app.py` | Gradio UI |
| `tests/test_pipeline.py` | Unit tests (no Ollama required) |
| `evaluation/evaluate.py` | Batch CLI evaluation |

## Language support

| Language | PDF extraction | LLM prompt | Output |
|---|---|---|---|
| Italian | ✅ | ✅ | ✅ |
| Arabic (RTL) | ✅ | ✅ | ✅ |
| English | ✅ | ✅ | ✅ |
| Auto-detect | ✅ | — | — |
