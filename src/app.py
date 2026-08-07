"""
app.py — PDF Concept Map Generator
Gradio interface: upload PDF → choose language & model → view concept map.
Author: Abdellatif El Majdoubi
GitHub: https://github.com/abdel-2000
"""

import json
import tempfile
import os

import gradio as gr
from PIL import Image
import io

from pdf_extractor import extract_text
from llm_mapper import generate_map
from graph_renderer import render_graph


# ── Helpers ───────────────────────────────────────────────────────────────

def process_pdf(pdf_file, language: str, model: str, max_chars: int):
    """Full pipeline: PDF → text → LLM → graph image + JSON."""
    if pdf_file is None:
        return None, "⚠️ Please upload a PDF file.", ""

    try:
        # 1. Extract text
        result = extract_text(pdf_file.name, max_chars=int(max_chars))
        text   = result["text"]
        lang_hint = result["language_hint"]

        if not text.strip():
            return None, "⚠️ No text could be extracted from this PDF.", ""

        status = (
            f"✅ Extracted {result['char_count']:,} characters "
            f"from {result['pages']} page(s). "
            f"Detected language: **{lang_hint}**. "
            + ("⚠️ Text was truncated." if result["truncated"] else "")
        )

        # Use detected language if auto
        effective_lang = lang_hint if language == "auto" else language

        # 2. Generate concept map via LLM
        concept_map = generate_map(text, language=effective_lang, model=model)

        # 3. Render graph
        png_bytes = render_graph(concept_map)
        image = Image.open(io.BytesIO(png_bytes))

        json_out = json.dumps(concept_map, ensure_ascii=False, indent=2)
        return image, status, json_out

    except FileNotFoundError as e:
        return None, f"❌ {e}", ""
    except ConnectionError as e:
        return None, f"❌ Ollama not running.\n{e}\n\nStart it with: `ollama serve`", ""
    except ValueError as e:
        return None, f"❌ LLM parsing error:\n{e}", ""
    except Exception as e:
        return None, f"❌ Unexpected error: {e}", ""


def check_ollama():
    """Check if Ollama is running and return status string."""
    import requests
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        models = [m["name"] for m in r.json().get("models", [])]
        if models:
            return f"✅ Ollama running. Available models: {', '.join(models)}"
        return "✅ Ollama running but no models found. Run: `ollama pull llama3`"
    except Exception:
        return "❌ Ollama not running. Start it with: `ollama serve`"


# ── Gradio UI ─────────────────────────────────────────────────────────────

CSS = """
h1 { color: #1B3A5C; }
.status-box { background: #F4F7FB; border-radius: 8px; padding: 10px; }
footer { display: none; }
"""

with gr.Blocks(
    title="PDF Concept Map Generator",
    theme=gr.themes.Soft(primary_hue="blue"),
    css=CSS,
) as demo:

    gr.Markdown("""
    # 🗺️ PDF Concept Map Generator
    Upload a PDF → choose language → get an interactive concept map powered by a local LLM (Ollama).

    **Supports:** 🇮🇹 Italian · 🇸🇦 Arabic · 🇬🇧 English
    """)

    with gr.Row():
        with gr.Column(scale=1):
            pdf_input = gr.File(
                label="📄 Upload PDF",
                file_types=[".pdf"],
            )
            language = gr.Radio(
                choices=["auto", "italian", "arabic", "english"],
                value="auto",
                label="🌐 Output language",
                info="'auto' detects Italian / Arabic / English automatically.",
            )
            model = gr.Textbox(
                value="llama3",
                label="🤖 Ollama model",
                info="Must be installed locally. Run: ollama pull llama3",
            )
            max_chars = gr.Slider(
                minimum=1000, maximum=12000, value=6000, step=500,
                label="📏 Max characters extracted",
                info="Reduce if the model is slow or runs out of memory.",
            )
            btn = gr.Button("🚀 Generate concept map", variant="primary")

            ollama_status = gr.Markdown(check_ollama())
            gr.Button("🔄 Check Ollama status", size="sm").click(
                fn=check_ollama, outputs=ollama_status
            )

        with gr.Column(scale=2):
            graph_out  = gr.Image(label="🗺️ Concept Map", type="pil")
            status_out = gr.Markdown(label="Status")
            json_out   = gr.Code(
                label="📋 Raw JSON (concept map)",
                language="json",
                visible=True,
            )

    btn.click(
        fn=process_pdf,
        inputs=[pdf_input, language, model, max_chars],
        outputs=[graph_out, status_out, json_out],
    )

    gr.Markdown("""
    ---
    ### ℹ️ How to use
    1. Install Ollama: [ollama.com](https://ollama.com)
    2. Pull a model: `ollama pull llama3`
    3. Start Ollama: `ollama serve`
    4. Upload a PDF and click **Generate**

    ### ⚠️ Limitations
    - Requires Ollama running locally (no internet needed)
    - Large PDFs are truncated to avoid token overflow
    - Arabic PDF extraction quality depends on the PDF encoding
    - Map quality depends on the chosen model

    ---
    *Built by [Abdellatif El Majdoubi](https://github.com/abdel-2000) · UNINETTUNO 2025/2026*
    """)


if __name__ == "__main__":
    demo.launch(share=False, server_port=7860)
