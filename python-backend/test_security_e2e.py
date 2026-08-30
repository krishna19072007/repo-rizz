"""
End-to-end verification: security score increases naturally through the engine.

Phase 18 — confirms that:
  1. A well-secured repo scores higher on the Security dimension than a poorly-secured one.
  2. The overall health score increases when security posture improves.
  3. Critical security findings appear for tracked env files and exposed keys.
  4. The security dimension is present in the final output dimensions list.
  5. Weighted contributions reflect the correct security weight.
"""
import pytest
from scoring import classify_repository, calculate_repository_score, calculate_resume_readiness
from analyzers import analyze_security, analyze_architecture, analyze_code_quality, analyze_documentation


# ---------------------------------------------------------------------------
# Helpers – build a realistic input_data dict (no network required)
# ---------------------------------------------------------------------------

def _base_input(tree, classification_type="APPLICATION"):
    """Minimal input_data that mimics what fetch_analysis_input produces."""
    return {
        "repo": {
            "name": "test-repo",
            "full_name": "test/test-repo",
            "description": "A test repository",
            "html_url": "https://github.com/test/test-repo",
            "default_branch": "main",
            "stargazers_count": 10,
            "owner": {"login": "test"},
        },
        "tree": tree,
        "importantFiles": {},
        "packageJson": {},
        "languages": {"Python": 100},
        "readme": "# Test\nThis is a test project.",
        "classification": classify_repository({
            "tree": tree,
            "repo": {"name": "test-repo", "full_name": "test/test-repo", "description": "A test repository"},
            "languages": {"Python": 100},
            "readme": "# Test\nThis is a test project.",
        }),
    }


def _run_engine(input_data):
    """Simulate the engine pipeline up to scoring (skips AI and GitHub calls)."""
    classification = classify_repository(input_data)
    input_data["classification"] = classification

    dimensions = [
        analyze_documentation(input_data),
        analyze_code_quality(input_data),
        analyze_architecture(input_data),
        analyze_security(input_data),
    ]

    input_data["dimension_scores"] = dimensions
    scoring_result = calculate_repository_score(input_data)
    return scoring_result


# ---------------------------------------------------------------------------
# Test fixtures – two contrasting repos
# ---------------------------------------------------------------------------

SECURED_TREE = [
    {"path": ".gitignore"},
    {"path": "package-lock.json"},
    {"path": "SECURITY.md"},
    {"path": ".github/dependabot.yml"},
    {"path": ".github/workflows/codeql-analysis.yml"},
    {"path": "README.md"},
    {"path": "src/main.py"},
]

INSECURED_TREE = [
    {"path": ".env"},
    {"path": ".env.local"},
    {"path": "id_rsa"},
    {"path": "README.md"},
    {"path": "src/main.py"},
]

MIXED_TREE = [
    {"path": ".gitignore"},
    {"path": "package-lock.json"},
    {"path": ".env"},
    {"path": "README.md"},
    {"path": "src/main.py"},
]


# ---------------------------------------------------------------------------
# 1. Security dimension scoring
# ---------------------------------------------------------------------------

class TestSecurityScoreFlow:
    def test_secured_beats_unsecured(self):
        secured = _run_engine(_base_input(SECURED_TREE))
        unsecured = _run_engine(_base_input(INSECURED_TREE))

        sec_dim = next(d for d in secured["dimensions"] if d["id"] == "security")
        unsec_dim = next(d for d in unsecured["dimensions"] if d["id"] == "security")

        assert sec_dim["score"] > unsec_dim["score"], (
            f"Secured ({sec_dim['score']}) should beat unsecured ({unsec_dim['score']})"
        )

    def test_secured_scores_high(self):
        result = _run_engine(_base_input(SECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        assert sec_dim["score"] >= 80

    def test_unsecured_scores_low(self):
        result = _run_engine(_base_input(INSECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        assert sec_dim["score"] <= 30

    def test_mixed_score_between_extremes(self):
        secured = _run_engine(_base_input(SECURED_TREE))
        unsecured = _run_engine(_base_input(INSECURED_TREE))
        mixed = _run_engine(_base_input(MIXED_TREE))

        sec_score = next(d for d in secured["dimensions"] if d["id"] == "security")["score"]
        unscore = next(d for d in unsecured["dimensions"] if d["id"] == "security")["score"]
        mixed_score = next(d for d in mixed["dimensions"] if d["id"] == "security")["score"]

        assert unscore <= mixed_score <= sec_score, (
            f"Mixed ({mixed_score}) should be between unsecured ({unscore}) and secured ({sec_score})"
        )


# ---------------------------------------------------------------------------
# 2. Overall health score increases with better security
# ---------------------------------------------------------------------------

class TestOverallScoreFlow:
    def test_overall_increases_with_security(self):
        secured = _run_engine(_base_input(SECURED_TREE))
        unsecured = _run_engine(_base_input(INSECURED_TREE))

        assert secured["overall"] > unsecured["overall"], (
            f"Overall secured ({secured['overall']}) should exceed "
            f"unsecured ({unsecured['overall']})"
        )

    def test_overall_is_between_0_and_100(self):
        for tree in [SECURED_TREE, INSECURED_TREE, MIXED_TREE]:
            result = _run_engine(_base_input(tree))
            assert 0 <= result["overall"] <= 100


# ---------------------------------------------------------------------------
# 3. Critical findings for tracked env and keys
# ---------------------------------------------------------------------------

class TestCriticalFindings:
    def test_env_tracked_produces_critical(self):
        result = _run_engine(_base_input(INSECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        critical = [f for f in sec_dim["findings"] if f["severity"] == "critical"]
        assert len(critical) >= 1
        ids = {f["id"] for f in critical}
        assert "sec-env" in ids

    def test_keys_tracked_produces_critical(self):
        result = _run_engine(_base_input(INSECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        critical = [f for f in sec_dim["findings"] if f["severity"] == "critical"]
        ids = {f["id"] for f in critical}
        assert "sec-keys" in ids

    def test_secured_repo_has_no_critical_security_findings(self):
        result = _run_engine(_base_input(SECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        critical = [f for f in sec_dim["findings"] if f["severity"] == "critical"]
        assert len(critical) == 0


# ---------------------------------------------------------------------------
# 4. Security dimension present in output
# ---------------------------------------------------------------------------

class TestSecurityDimensionPresence:
    def test_security_dimension_in_output(self):
        result = _run_engine(_base_input(SECURED_TREE))
        sec_dims = [d for d in result["dimensions"] if d["id"] == "security"]
        assert len(sec_dims) == 1

    def test_security_dimension_has_signals(self):
        result = _run_engine(_base_input(SECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        assert len(sec_dim["signals"]) == 7

    def test_security_dimension_has_strengths_when_present(self):
        result = _run_engine(_base_input(SECURED_TREE))
        sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
        assert len(sec_dim["strengths"]) >= 3


# ---------------------------------------------------------------------------
# 5. Weighted contributions reflect security weight
# ---------------------------------------------------------------------------

class TestWeightedContributions:
    def test_security_contribution_exists(self):
        result = _run_engine(_base_input(SECURED_TREE))
        security_contribs = [
            c for c in result["weightedContributions"]
            if c["dimension"] == "security"
        ]
        assert len(security_contribs) == 1

    def test_security_contribution_weight_positive(self):
        result = _run_engine(_base_input(SECURED_TREE))
        security_contrib = next(
            c for c in result["weightedContributions"]
            if c["dimension"] == "security"
        )
        assert security_contrib["effectiveWeight"] > 0
        assert security_contrib["applicable"] is True


# ---------------------------------------------------------------------------
# 6. Monotonic improvement: adding each security signal increases score
# ---------------------------------------------------------------------------

class TestMonotonicImprovement:
    def test_score_increases_monotonically(self):
        """Each additional security control should not decrease the score."""
        progressive_trees = [
            # Baseline: nothing security-related
            [{"path": "README.md"}],
            # Add gitignore
            [{"path": "README.md"}, {"path": ".gitignore"}],
            # Add lockfile
            [{"path": "README.md"}, {"path": ".gitignore"}, {"path": "package-lock.json"}],
            # Add security md
            [{"path": "README.md"}, {"path": ".gitignore"}, {"path": "package-lock.json"}, {"path": "SECURITY.md"}],
            # Add dependabot
            [{"path": "README.md"}, {"path": ".gitignore"}, {"path": "package-lock.json"}, {"path": "SECURITY.md"}, {"path": ".github/dependabot.yml"}],
            # Add security CI
            [{"path": "README.md"}, {"path": ".gitignore"}, {"path": "package-lock.json"}, {"path": "SECURITY.md"}, {"path": ".github/dependabot.yml"}, {"path": ".github/workflows/codeql-analysis.yml"}],
        ]

        scores = []
        for tree in progressive_trees:
            result = _run_engine(_base_input(tree))
            sec_dim = next(d for d in result["dimensions"] if d["id"] == "security")
            scores.append(sec_dim["score"])

        for i in range(1, len(scores)):
            assert scores[i] >= scores[i - 1], (
                f"Score decreased from step {i-1} ({scores[i-1]}) to step {i} ({scores[i]})"
            )
