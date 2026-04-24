"""Test suite for extractor modules.

Run: pytest tests/test_extractors.py -v
Coverage: pytest --cov=extractors tests/test_extractors.py
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from extractors.file_parser import FileParser
from extractors.persona_extractor import PersonaExtractor, PersonaInfo
from extractors.universal_extractor import (
    UniversalExtractor,
    DocumentType,
    ExtractedInfo,
    LLMBackend,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FileParser Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFileParser:
    """Tests for FileParser utility class."""

    def test_detect_file_type_pdf(self):
        assert FileParser.detect_file_type("doc.pdf") == "pdf"
        assert FileParser.detect_file_type("doc.PDF") == "pdf"

    def test_detect_file_type_docx(self):
        assert FileParser.detect_file_type("report.docx") == "docx"
        assert FileParser.detect_file_type("doc.DOCX") == "docx"

    def test_detect_file_type_txt(self):
        assert FileParser.detect_file_type("notes.txt") == "text"
        assert FileParser.detect_file_type("notes.md") == "text"

    def test_detect_file_type_csv(self):
        assert FileParser.detect_file_type("data.csv") == "csv"
        assert FileParser.detect_file_type("data.CSV") == "csv"

    def test_is_supported(self):
        assert FileParser.is_supported("test.pdf") is True
        assert FileParser.is_supported("test.docx") is True
        assert FileParser.is_supported("test.txt") is True
        assert FileParser.is_supported("test.csv") is True
        assert FileParser.is_supported("test.json") is True
        assert FileParser.is_supported("test.exe") is False
        assert FileParser.is_supported("test.png") is False

    def test_parse_text_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("Hello, world!")
            path = f.name

        parser = FileParser()
        result = parser.parse(path)

        assert result["content"] == "Hello, world!"
        assert result["format"] == "text"
        assert result["metadata"]["filename"].endswith(".txt")

        Path(path).unlink()

    def test_parse_nonexistent_file(self):
        parser = FileParser()
        with pytest.raises((FileNotFoundError, ValueError)):
            parser.parse("/nonexistent/file.txt")

    def test_parse_multiple(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            a_path = Path(tmpdir) / "a.txt"
            b_path = Path(tmpdir) / "b.txt"
            a_path.write_text("内容A", encoding="utf-8")
            b_path.write_text("内容B", encoding="utf-8")

            parser = FileParser()
            results = parser.parse_multiple([str(a_path), str(b_path)])

            # Keys are absolute paths, not just filenames
            assert str(a_path) in results
            assert str(b_path) in results
            assert results[str(a_path)]["content"] == "内容A"
            assert results[str(b_path)]["content"] == "内容B"


# ═══════════════════════════════════════════════════════════════════════════════
# PersonaExtractor Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestPersonaExtractor:
    """Tests for PersonaExtractor."""

    def test_extract_name(self):
        extractor = PersonaExtractor()
        text = "姓名：张三\n职位：高级工程师\n公司：ABC科技"
        result = extractor.extract(text)

        # Returns PersonaInfo dataclass
        assert isinstance(result, PersonaInfo)
        assert result.name == "张三"

    def test_extract_title(self):
        extractor = PersonaExtractor()
        text = "姓名：张三\n职位：工程师"
        result = extractor.extract(text)

        assert isinstance(result, PersonaInfo)
        assert result.title == "工程师"

    def test_extract_empty_text(self):
        extractor = PersonaExtractor()
        result = extractor.extract("")

        assert isinstance(result, PersonaInfo)
        assert result.name == ""
        assert result.title == ""

    def test_to_dict(self):
        info = PersonaInfo(name="张三", title="工程师")
        d = info.to_dict()
        assert d["name"] == "张三"
        assert d["title"] == "工程师"
        assert "basic_intro" in d


# ═══════════════════════════════════════════════════════════════════════════════
# UniversalExtractor Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestUniversalExtractor:
    """Tests for UniversalExtractor."""

    def test_extracted_info_structure(self):
        info = ExtractedInfo(
            document_type=DocumentType.UNKNOWN,
            document_type_name="unknown",
            name="Test",
            title="Title",
        )

        assert info.document_type == DocumentType.UNKNOWN
        assert info.document_type_name == "unknown"
        assert info.name == "Test"
        assert info.key_points == []

    def test_document_type_enum(self):
        assert DocumentType.RESUME.value == "resume"
        assert DocumentType.CHAT_LOGS.value == "chat_logs"
        assert DocumentType.UNKNOWN.value == "unknown"

    def test_parse_json_fuzzy(self):
        extractor = UniversalExtractor()
        # Test with markdown-wrapped JSON
        text = "```json\n{\"name\": \"Test\", \"value\": 42}\n```"
        result = extractor._parse_json_fuzzy(text)

        assert result["name"] == "Test"
        assert result["value"] == 42

    def test_parse_json_fuzzy_invalid(self):
        extractor = UniversalExtractor()
        result = extractor._parse_json_fuzzy("not json at all")
        # Returns empty-ish structure, not bare {} (due to safe defaults)
        assert result.get("name", "") == ""
        assert result.get("key_points", "not_list") == []

    def test_llm_backend_fallback(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            backend = LLMBackend()
            # When env var is empty, api_key should be empty
            assert backend.api_key == "" or backend.api_key is None


# ═══════════════════════════════════════════════════════════════════════════════
# ChatParser Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestChatParser:
    """Tests for chat log parser."""

    def test_parse_chat_format(self):
        from extractors.chat_parser import ChatParser

        parser = ChatParser()
        # Use wechat_txt format (requires HH:MM:SS timestamp)
        sample_chat = """2024-01-01 10:00:00 张三
你好
2024-01-01 10:01:00 李四
你好，有事吗？"""
        result = parser.parse(sample_chat)

        assert isinstance(result, list)
        assert len(result) > 0
        assert "张三" in str(result)


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """End-to-end integration tests."""

    def test_end_to_end_with_text(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as f:
            f.write("This is a test document about Python programming.")
            path = f.name

        parser = FileParser()
        parsed = parser.parse(path)

        assert "content" in parsed
        assert "Python" in parsed["content"]

        Path(path).unlink()

    def test_universal_extractor_with_mock(self):
        extractor = UniversalExtractor()
        mock_backend = MagicMock()
        mock_backend.complete.return_value = json.dumps({
            "document_type": "technical_docs",
            "name": "Python Guide",
            "key_points": ["Python basics"],
        })
        extractor.llm = mock_backend

        result = extractor.extract("Python is a programming language.")

        assert isinstance(result, ExtractedInfo)
        assert result.name == "Python Guide"
