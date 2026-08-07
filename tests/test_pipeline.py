"""
Unit tests for pdf_extractor and llm_mapper (parsing only — no Ollama required).
Run: pytest tests/ -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from pdf_extractor import _clean_text, _detect_language
from llm_mapper import _parse_json, _validate


# ── pdf_extractor tests ───────────────────────────────────────────────────

class TestCleanText:
    def test_removes_extra_newlines(self):
        text = "hello\n\n\n\nworld"
        result = _clean_text(text)
        assert "\n\n\n" not in result

    def test_removes_extra_spaces(self):
        text = "hello    world"
        result = _clean_text(text)
        assert "  " not in result

    def test_strips(self):
        text = "   hello   "
        assert _clean_text(text) == "hello"


class TestDetectLanguage:
    def test_arabic(self):
        text = "مرحبا بك في عالم تحليل البيانات والذكاء الاصطناعي"
        assert _detect_language(text) == "arabic"

    def test_italian(self):
        text = "questo documento descrive come funziona la data analytics nella gestione aziendale"
        assert _detect_language(text) == "italian"

    def test_english(self):
        text = "this document describes how data analytics works in business management"
        assert _detect_language(text) == "english"

    def test_empty(self):
        assert _detect_language("") == "unknown"


# ── llm_mapper tests ──────────────────────────────────────────────────────

VALID_JSON = '''{
  "title": "Data Analytics",
  "nodes": [
    {"id": "1", "label": "KPI", "type": "main"},
    {"id": "2", "label": "Metrics", "type": "sub"}
  ],
  "edges": [
    {"from": "1", "to": "2", "label": "includes"}
  ]
}'''

class TestParseJson:
    def test_clean_json(self):
        result = _parse_json(VALID_JSON)
        assert result["title"] == "Data Analytics"
        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1

    def test_json_with_markdown(self):
        wrapped = f"```json\n{VALID_JSON}\n```"
        result = _parse_json(wrapped)
        assert result["title"] == "Data Analytics"

    def test_json_with_preamble(self):
        text = f"Here is the concept map:\n{VALID_JSON}\nEnd."
        result = _parse_json(text)
        assert "nodes" in result

    def test_invalid_json_raises(self):
        with pytest.raises(ValueError):
            _parse_json("This is not JSON at all.")


class TestValidate:
    def test_adds_edges_if_missing(self):
        data = {"title": "T", "nodes": [{"id": "1", "label": "A"}]}
        result = _validate(data)
        assert result["edges"] == []

    def test_adds_title_if_missing(self):
        data = {"nodes": [{"id": "1", "label": "A"}], "edges": []}
        result = _validate(data)
        assert result["title"] == "Concept Map"

    def test_adds_id_if_missing(self):
        data = {"title": "T", "nodes": [{"label": "A"}], "edges": []}
        result = _validate(data)
        assert result["nodes"][0]["id"] == "1"

    def test_raises_if_no_nodes(self):
        with pytest.raises(ValueError):
            _validate({"title": "T", "edges": []})
