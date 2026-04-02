# ABOUTME: Tests for AI provider transparency checks
# ABOUTME: Verifies detection of AI providers and transparency status evaluation

"""
Tests for provider checks.
"""

from pathlib import Path

from ethica.checks.base import CheckStatus
from ethica.checks.provider_checks import ProviderCheck


class TestProviderCheck:
    def _make_check(self, config=None):
        return ProviderCheck({
            "id": "test-provider",
            "name": "Test Provider Check",
            "principle": "transparency",
            "severity": "warning",
            "description": "Test",
            "config": config or {},
        })

    def test_detects_anthropic_from_python_import(self, tmp_path):
        """Detects Anthropic from Python import statement."""
        src = tmp_path / "app.py"
        src.write_text('from anthropic import Anthropic\nclient = Anthropic()\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "Anthropic" in result.message

    def test_detects_openai_from_python_import(self, tmp_path):
        """Detects OpenAI from Python import statement."""
        src = tmp_path / "main.py"
        src.write_text('import openai\nclient = openai.OpenAI()\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "OpenAI" in result.message

    def test_detects_provider_from_model_id_string(self, tmp_path):
        """Detects provider from model ID string in code."""
        src = tmp_path / "chat.py"
        src.write_text('model = "claude-sonnet-4-5-20250514"\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "Anthropic" in result.message

    def test_detects_provider_from_package_json(self, tmp_path):
        """Detects provider from package.json dependency."""
        pkg = tmp_path / "package.json"
        pkg.write_text('{"dependencies": {"@anthropic-ai/sdk": "^1.0"}}')

        check = self._make_check()
        result = check.run(tmp_path)

        # Falls back to dep files when no source files found
        assert result.status == CheckStatus.PASSED
        assert "Anthropic" in result.message

    def test_detects_opaque_provider(self, tmp_path):
        """Flags providers that don't publish system cards."""
        src = tmp_path / "app.py"
        src.write_text('import mistralai\nclient = mistralai.Mistral()\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.FAILED
        assert "Mistral" in result.message

    def test_mixed_transparent_and_opaque(self, tmp_path):
        """Reports failure when any provider lacks system cards."""
        src = tmp_path / "app.py"
        src.write_text(
            'import anthropic\n'
            'import mistralai\n'
        )

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.FAILED
        assert "Anthropic" in result.message
        assert "Mistral" in result.message

    def test_no_ai_providers_skipped(self, tmp_path):
        """Skips when no AI providers detected."""
        src = tmp_path / "app.py"
        src.write_text('import json\nprint("hello")\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.SKIPPED

    def test_skips_node_modules(self, tmp_path):
        """Does not scan inside node_modules."""
        (tmp_path / "node_modules" / "openai").mkdir(parents=True)
        (tmp_path / "node_modules" / "openai" / "index.js").write_text(
            'module.exports = require("openai")'
        )
        # No source files outside node_modules
        src = tmp_path / "app.py"
        src.write_text('print("no ai here")\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.SKIPPED

    def test_detects_js_import(self, tmp_path):
        """Detects provider from JavaScript/TypeScript import."""
        src = tmp_path / "index.ts"
        src.write_text('import OpenAI from "openai";\nconst client = new OpenAI();\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "OpenAI" in result.message

    def test_detects_google_genai(self, tmp_path):
        """Detects Google GenAI from import."""
        src = tmp_path / "app.py"
        src.write_text('import google.generativeai as genai\nmodel = genai.GenerativeModel("gemini-2.5-pro")\n')

        check = self._make_check()
        result = check.run(tmp_path)

        assert result.status == CheckStatus.PASSED
        assert "Google" in result.message
