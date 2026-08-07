"""
evaluate.py — Batch evaluation of the concept map pipeline.
Runs the full pipeline on all PDFs in a folder and saves results.

Usage:
    python evaluation/evaluate.py --input data/ --model llama3 --language italian
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from pdf_extractor import extract_text
from llm_mapper import generate_map
from graph_renderer import render_graph


def evaluate_folder(folder: str, model: str, language: str) -> None:
    pdf_files = [f for f in os.listdir(folder) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in {folder}")
        return

    print(f"\n{'='*60}")
    print(f"  PDF CONCEPT MAP – EVALUATION REPORT")
    print(f"  Model: {model} | Language: {language}")
    print(f"  PDFs found: {len(pdf_files)}")
    print(f"{'='*60}\n")

    for fname in pdf_files:
        path = os.path.join(folder, fname)
        print(f"Processing: {fname}")
        t0 = time.time()
        try:
            result   = extract_text(path)
            cmap     = generate_map(result["text"], language=language, model=model)
            elapsed  = time.time() - t0

            print(f"  ✅ {len(cmap['nodes'])} nodes, {len(cmap['edges'])} edges — {elapsed:.1f}s")
            print(f"  Title: {cmap['title']}")

            # Save JSON
            out_path = path.replace(".pdf", "_map.json")
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(cmap, f, ensure_ascii=False, indent=2)
            print(f"  Saved: {out_path}")

        except ConnectionError:
            print("  ❌ Ollama not running — start with: ollama serve")
            break
        except Exception as e:
            print(f"  ❌ Error: {e}")
        print()

    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Batch concept map evaluation.")
    parser.add_argument("--input",    default="data/",    help="Folder with PDF files")
    parser.add_argument("--model",    default="llama3",   help="Ollama model name")
    parser.add_argument("--language", default="italian",  help="Output language")
    args = parser.parse_args()
    evaluate_folder(args.input, args.model, args.language)


if __name__ == "__main__":
    main()
