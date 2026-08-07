"""
llm_mapper.py
Sends extracted text to Ollama and parses the concept map JSON response.
Supports: Italian, Arabic, English output.
"""

import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"

PROMPTS = {
    "italian": """Sei un esperto di analisi del testo. Leggi il testo seguente ed estrai una mappa concettuale.

Rispondi SOLO con un oggetto JSON valido, senza testo aggiuntivo, senza markdown, senza backtick.
Il JSON deve avere questa struttura esatta:
{
  "title": "Titolo principale del documento",
  "nodes": [
    {"id": "1", "label": "Concetto principale", "type": "main"},
    {"id": "2", "label": "Sotto-concetto", "type": "sub"}
  ],
  "edges": [
    {"from": "1", "to": "2", "label": "include"}
  ]
}

Regole:
- Massimo 12 nodi
- I nodi "main" sono i concetti più importanti (max 3)
- I nodi "sub" sono i concetti secondari
- Le etichette degli archi descrivono la relazione (es: "include", "causa", "è un tipo di")
- Rispondi in italiano

TESTO:
""",
    "arabic": """أنت خبير في تحليل النصوص. اقرأ النص التالي واستخرج خريطة مفاهيمية.

أجب فقط بكائن JSON صالح، بدون نص إضافي، بدون markdown، بدون backticks.
يجب أن يكون لـ JSON هذا الهيكل:
{
  "title": "العنوان الرئيسي للوثيقة",
  "nodes": [
    {"id": "1", "label": "المفهوم الرئيسي", "type": "main"},
    {"id": "2", "label": "المفهوم الفرعي", "type": "sub"}
  ],
  "edges": [
    {"from": "1", "to": "2", "label": "يتضمن"}
  ]
}

القواعد:
- 12 عقدة كحد أقصى
- عقد "main" هي المفاهيم الأكثر أهمية (3 كحد أقصى)
- عقد "sub" هي المفاهيم الثانوية
- أجب باللغة العربية

النص:
""",
    "english": """You are an expert text analyst. Read the following text and extract a concept map.

Reply ONLY with a valid JSON object, no extra text, no markdown, no backticks.
The JSON must have this exact structure:
{
  "title": "Main document title",
  "nodes": [
    {"id": "1", "label": "Main concept", "type": "main"},
    {"id": "2", "label": "Sub-concept", "type": "sub"}
  ],
  "edges": [
    {"from": "1", "to": "2", "label": "includes"}
  ]
}

Rules:
- Maximum 12 nodes
- "main" nodes are the most important concepts (max 3)
- "sub" nodes are secondary concepts
- Edge labels describe the relationship
- Reply in English

TEXT:
""",
}


def generate_map(
    text: str,
    language: str = "italian",
    model: str = "llama3",
    timeout: int = 120,
) -> dict:
    """
    Call Ollama to generate a concept map from text.

    Args:
        text:     Extracted PDF text.
        language: Output language — 'italian', 'arabic', 'english'.
        model:    Ollama model name.
        timeout:  Request timeout in seconds.

    Returns:
        Parsed concept map dict with keys: title, nodes, edges.

    Raises:
        ConnectionError: If Ollama is not running.
        ValueError: If the LLM response cannot be parsed as JSON.
    """
    if language not in PROMPTS:
        language = "english"

    prompt = PROMPTS[language] + text

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=timeout,
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            "Cannot connect to Ollama. Make sure it is running: `ollama serve`"
        )
    except requests.exceptions.Timeout:
        raise TimeoutError(f"Ollama did not respond within {timeout} seconds.")

    raw = response.json().get("response", "")
    return _parse_json(raw)


def _parse_json(raw: str) -> dict:
    """Extract and validate JSON from LLM response."""
    # Remove markdown code blocks if present
    raw = re.sub(r'```json\s*', '', raw)
    raw = re.sub(r'```\s*', '', raw)
    raw = raw.strip()

    # Try direct parse first
    try:
        data = json.loads(raw)
        return _validate(data)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object inside the string
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group())
            return _validate(data)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse LLM response as JSON.\nRaw response:\n{raw[:500]}"
    )


def _validate(data: dict) -> dict:
    """Ensure required keys exist and apply defaults."""
    if "nodes" not in data:
        raise ValueError("JSON missing 'nodes' key.")
    if "edges" not in data:
        data["edges"] = []
    if "title" not in data:
        data["title"] = "Concept Map"

    # Ensure each node has required fields
    for i, node in enumerate(data["nodes"]):
        if "id" not in node:
            node["id"] = str(i + 1)
        if "label" not in node:
            node["label"] = f"Node {i + 1}"
        if "type" not in node:
            node["type"] = "sub"

    return data
