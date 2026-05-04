"""Tests for prompt protocol requirements — active prompts only."""

import pytest

from fu7ur3pr00f.prompts.loader import load_prompt

pytestmark = pytest.mark.unit


class TestAnalyzeGapsColdStart:
    """Tests for Cold Start Protocol in analyze_gaps.md."""

    def test_cold_start_in_analyze_gaps(self):
        """Cold Start Protocol should also be referenced in analyze_gaps prompt."""
        content = load_prompt("analyze_gaps")
        assert "Cold Start" in content or "Day 0" in content or "blueprint" in content.lower()

    def test_analyze_gaps_has_cold_start_step(self):
        """Verify analyze_gaps includes Cold Start Protocol step."""
        content = load_prompt("analyze_gaps")
        assert "Cold Start" in content

    def test_analyze_gaps_cold_start_provides_blueprint(self):
        """Cold Start in analyze_gaps must provide Day 0 blueprint."""
        content = load_prompt("analyze_gaps")
        assert any(
            term in content.lower()
            for term in ["blueprint", "day 0", "first project", "create github"]
        )

    def test_analyze_gaps_cold_start_has_dual_metrics(self):
        """Cold Start actions should have Goal Impact + Sovereignty scores."""
        content = load_prompt("analyze_gaps")
        assert "Goal Impact" in content
        assert "Sovereignty" in content


class TestSubstanceOverSyntax:
    """Tests for Substance-over-Syntax rule in generate_cv.md."""

    def test_substance_over_syntax_rule_exists(self):
        """Verify Substance-over-Syntax rule is defined in generate_cv prompt."""
        content = load_prompt("generate_cv")
        assert "Substance-over-Syntax" in content or "Substance over Syntax" in content

    def test_substance_over_syntax_requires_evidence(self):
        """Substance-over-Syntax must require evidence for claims."""
        content = load_prompt("generate_cv")
        assert "Signature Achievement" in content
        assert "backed by" in content.lower() or "evidence" in content.lower()

    def test_weak_vs_strong_examples_provided(self):
        """Prompt should provide examples of weak vs strong openers."""
        content = load_prompt("generate_cv")
        assert "Weak:" in content
        assert "Strong:" in content

    def test_banned_openers_mentioned(self):
        """Prompt should mention banned weak openers."""
        content = load_prompt("generate_cv")
        assert any(
            phrase in content
            for phrase in [
                "years of experience",
                "Results-driven",
                "Passionate about",
                "proven track record",
            ]
        )

    def test_xyz_formula_required(self):
        """CV bullets must follow XYZ formula."""
        content = load_prompt("generate_cv")
        assert "XYZ" in content
        assert "Accomplished" in content
        assert "measured by" in content

    def test_action_verb_rules_defined(self):
        """Prompt should define action verb rules."""
        content = load_prompt("generate_cv")
        assert "Action Verb" in content
        assert any(
            verb in content for verb in ["Architected", "Shipped", "Drove", "Migrated", "Pioneered"]
        )


class TestDataFidelity:
    """Tests for data fidelity rules — preventing hallucination."""

    def test_synthesis_requires_github_data_for_repo_claims(self):
        """Synthesis prompt must forbid mentioning repo names without tool data."""
        content = load_prompt("synthesis")
        content_lower = content.lower()
        assert "data fidelity" in content_lower
        assert (
            "cannot mention specific repo names" in content_lower
            or "unless they appear" in content_lower
        )
        assert "do not invent" in content_lower or "never invent" in content_lower
