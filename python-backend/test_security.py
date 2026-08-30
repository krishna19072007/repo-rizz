import pytest
from analyzers import analyze_security, create_finding, create_dimension


# ---------------------------------------------------------------------------
# Helpers – minimal input_data builder
# ---------------------------------------------------------------------------

def _make_input(tree=None, important_files=None, security_content=None,
                classification_type="UNKNOWN"):
    """Return a minimal input_data dict accepted by analyze_security."""
    tree = tree or []
    important_files = important_files or {}
    input_data = {
        "tree": tree,
        "importantFiles": important_files,
        "classification": {"type": classification_type, "confidence": 0.8},
    }
    if security_content is not None:
        input_data["security"] = security_content
    return input_data


# ---------------------------------------------------------------------------
# 1. gitignore signal
# ---------------------------------------------------------------------------

class TestGitignoreSignal:
    def test_present_when_gitignore_exists(self):
        result = analyze_security(_make_input(tree=[{"path": ".gitignore"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["gitignore"]["status"] == "PRESENT"
        assert "positive" in [f["severity"] for f in result["findings"]
                              if f["id"] == "sec-gitignore"]

    def test_absent_when_no_gitignore(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["gitignore"]["status"] == "ABSENT"

    def test_gitignore_weight_is_15(self):
        result = analyze_security(_make_input(tree=[{"path": ".gitignore"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["gitignore"]["weight"] == 15


# ---------------------------------------------------------------------------
# 2. lockfile signal
# ---------------------------------------------------------------------------

class TestLockfileSignal:
    @pytest.mark.parametrize("lockfile", [
        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum",
        "requirements.txt",
    ])
    def test_detected_for_each_lockfile(self, lockfile):
        result = analyze_security(_make_input(tree=[{"path": lockfile}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["lockfile"]["status"] == "PRESENT"

    def test_absent_when_no_lockfile(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["lockfile"]["status"] == "ABSENT"

    def test_not_applicable_for_curated_list(self):
        result = analyze_security(_make_input(
            tree=[{"path": "README.md"}],
            classification_type="CURATED_LIST",
        ))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["lockfile"]["applicability"] == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# 3. security_md signal
# ---------------------------------------------------------------------------

class TestSecurityMdSignal:
    def test_present_via_tree(self):
        result = analyze_security(_make_input(tree=[{"path": "SECURITY.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_md"]["status"] == "PRESENT"

    def test_present_via_input_field(self):
        result = analyze_security(_make_input(security_content="# Security"))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_md"]["status"] == "PRESENT"

    def test_absent(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_md"]["status"] == "ABSENT"

    def test_missing_generates_info_finding(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        sec_findings = [f for f in result["findings"] if f["id"] == "sec-security_md"]
        assert len(sec_findings) == 1
        assert sec_findings[0]["severity"] == "info"


# ---------------------------------------------------------------------------
# 4. dependabot signal
# ---------------------------------------------------------------------------

class TestDependabotSignal:
    def test_present_yml(self):
        result = analyze_security(_make_input(
            tree=[{"path": ".github/dependabot.yml"}],
        ))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["dependabot"]["status"] == "PRESENT"

    def test_present_yaml(self):
        result = analyze_security(_make_input(
            tree=[{"path": ".github/dependabot.yaml"}],
        ))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["dependabot"]["status"] == "PRESENT"

    def test_absent(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["dependabot"]["status"] == "ABSENT"

    def test_missing_generates_low_finding(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        sec_findings = [f for f in result["findings"] if f["id"] == "sec-dependabot"]
        assert len(sec_findings) == 1
        assert sec_findings[0]["severity"] == "low"

    def test_not_applicable_for_curated_list(self):
        result = analyze_security(_make_input(
            tree=[{"path": "README.md"}],
            classification_type="CURATED_LIST",
        ))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["dependabot"]["applicability"] == "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# 5. security_ci signal
# ---------------------------------------------------------------------------

class TestSecurityCiSignal:
    def test_present_codeql(self):
        tree = [{"path": ".github/workflows/codeql-analysis.yml"}]
        result = analyze_security(_make_input(tree=tree))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_ci"]["status"] == "PRESENT"

    def test_present_snyk(self):
        tree = [{"path": ".github/workflows/snyk-scan.yml"}]
        result = analyze_security(_make_input(tree=tree))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_ci"]["status"] == "PRESENT"

    def test_present_trivy(self):
        tree = [{"path": ".github/workflows/trivy.yml"}]
        result = analyze_security(_make_input(tree=tree))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_ci"]["status"] == "PRESENT"

    def test_absent_with_non_security_workflow(self):
        tree = [{"path": ".github/workflows/deploy.yml"}]
        result = analyze_security(_make_input(tree=tree))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["security_ci"]["status"] == "ABSENT"

    def test_missing_generates_low_finding(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        sec_findings = [f for f in result["findings"]
                        if f["id"] == "sec-security_ci"]
        assert len(sec_findings) == 1
        assert sec_findings[0]["severity"] == "low"


# ---------------------------------------------------------------------------
# 6. no_tracked_env signal (credentials exposure)
# ---------------------------------------------------------------------------

class TestNoTrackedEnvSignal:
    @pytest.mark.parametrize("env_file", [
        ".env", ".env.local", ".env.production", ".env.development",
    ])
    def test_detected_for_each_env_file(self, env_file):
        result = analyze_security(_make_input(tree=[{"path": env_file}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_tracked_env"]["status"] == "ABSENT"

    def test_dotenv_star_pattern(self):
        result = analyze_security(_make_input(tree=[{"path": ".env.testing"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_tracked_env"]["status"] == "ABSENT"

    def test_present_when_no_env_files(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_tracked_env"]["status"] == "PRESENT"

    def test_tracked_env_generates_critical_finding(self):
        result = analyze_security(_make_input(tree=[{"path": ".env"}]))
        sec_findings = [f for f in result["findings"] if f["id"] == "sec-env"]
        assert len(sec_findings) == 1
        assert sec_findings[0]["severity"] == "critical"

    def test_raw_metrics_track_env_count(self):
        result = analyze_security(_make_input(
            tree=[{"path": ".env"}, {"path": ".env.local"}],
        ))
        assert result["rawMetrics"]["hasTrackedEnv"] is True
        assert result["rawMetrics"]["envFileCount"] == 2


# ---------------------------------------------------------------------------
# 7. no_keys signal (private key exposure)
# ---------------------------------------------------------------------------

class TestNoKeysSignal:
    @pytest.mark.parametrize("key_file", [
        "server.pem", "server.key", "cert.p12", "keystore.pfx",
        "truststore.jks", "id_rsa", "id_ed25519", "id_dsa", "id_ecdsa",
        "app.keystore",
    ])
    def test_detected_for_each_key_type(self, key_file):
        result = analyze_security(_make_input(tree=[{"path": key_file}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_keys"]["status"] == "ABSENT"

    def test_present_when_no_keys(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_keys"]["status"] == "PRESENT"

    def test_key_in_subdirectory(self):
        result = analyze_security(_make_input(
            tree=[{"path": "certs/server.pem"}],
        ))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_keys"]["status"] == "ABSENT"

    def test_tracked_keys_generates_critical_finding(self):
        result = analyze_security(_make_input(tree=[{"path": "id_rsa"}]))
        sec_findings = [f for f in result["findings"] if f["id"] == "sec-keys"]
        assert len(sec_findings) == 1
        assert sec_findings[0]["severity"] == "critical"

    def test_raw_metrics_track_key_count(self):
        result = analyze_security(_make_input(
            tree=[{"path": "id_rsa"}, {"path": "server.pem"}],
        ))
        assert result["rawMetrics"]["keyFileCount"] == 2


# ---------------------------------------------------------------------------
# 8. Docker security finding (not a signal, but a finding check)
# ---------------------------------------------------------------------------

class TestDockerSecurity:
    def test_dockerfile_without_dockerignore(self):
        tree = [{"path": "Dockerfile"}, {"path": "README.md"}]
        result = analyze_security(_make_input(tree=tree))
        docker_findings = [f for f in result["findings"]
                           if f["id"] == "sec-docker"]
        assert len(docker_findings) == 1
        assert docker_findings[0]["severity"] == "warning"

    def test_dockerfile_with_dockerignore(self):
        tree = [{"path": "Dockerfile"}, {"path": ".dockerignore"}, {"path": "README.md"}]
        result = analyze_security(_make_input(tree=tree))
        docker_findings = [f for f in result["findings"]
                           if f["id"] == "sec-docker"]
        assert len(docker_findings) == 0

    def test_no_dockerfile_no_finding(self):
        result = analyze_security(_make_input(tree=[{"path": "README.md"}]))
        docker_findings = [f for f in result["findings"]
                           if f["id"] == "sec-docker"]
        assert len(docker_findings) == 0

    def test_raw_metrics_track_docker(self):
        result = analyze_security(_make_input(
            tree=[{"path": "Dockerfile"}],
        ))
        assert result["rawMetrics"]["hasDockerfile"] is True


# ---------------------------------------------------------------------------
# 9. Scoring behavior
# ---------------------------------------------------------------------------

class TestScoring:
    def test_perfect_score_all_present(self):
        """A repo with all positive signals should score 100."""
        tree = [
            {"path": ".gitignore"},
            {"path": "package-lock.json"},
            {"path": "SECURITY.md"},
            {"path": ".github/dependabot.yml"},
            {"path": ".github/workflows/codeql-analysis.yml"},
        ]
        result = analyze_security(_make_input(tree=tree))
        assert result["score"] == 100
        assert result["status"] == "exceptional"

    def test_zero_score_nothing_present(self):
        """A repo with all negative signals should score 0."""
        tree = [
            {"path": ".env"},
            {"path": "id_rsa"},
        ]
        result = analyze_security(_make_input(tree=tree))
        assert result["score"] == 0
        assert result["status"] == "weak"

    def test_partial_score(self):
        """A repo with some positive signals scores between 0 and 100."""
        tree = [
            {"path": ".gitignore"},
            {"path": "package-lock.json"},
            # missing: security_md, dependabot, security_ci
            # env files & keys absent (positive)
        ]
        result = analyze_security(_make_input(tree=tree))
        # gitignore(15) + lockfile(15) + no_env(20) + no_keys(20) = 70/100
        assert 50 <= result["score"] <= 100

    def test_curated_list_excludes_non_applicable_weight(self):
        """Curated lists skip lockfile, dependabot, security_ci from scoring."""
        tree = [{"path": ".gitignore"}]  # only gitignore present
        result = analyze_security(_make_input(
            tree=tree, classification_type="CURATED_LIST",
        ))
        # Applicable: gitignore(15), security_md(10), no_env(20), no_keys(20) = 65
        # Earned: gitignore(15), no_env(20), no_keys(20) = 55
        # Score = 55/65 ≈ 85
        assert 80 <= result["score"] <= 100

    def test_score_is_always_between_0_and_100(self):
        """Score must be bounded."""
        for tree in [
            [],
            [{"path": ".env"}, {"path": "id_rsa"}],
            [{"path": ".gitignore"}, {"path": "SECURITY.md"}],
        ]:
            result = analyze_security(_make_input(tree=tree))
            assert 0 <= result["score"] <= 100


# ---------------------------------------------------------------------------
# 10. Finding structure validation
# ---------------------------------------------------------------------------

class TestFindingStructure:
    def test_findings_have_required_fields(self):
        tree = [{"path": ".env"}, {"path": "id_rsa"}, {"path": "README.md"}]
        result = analyze_security(_make_input(tree=tree))
        for finding in result["findings"]:
            assert "id" in finding
            assert "severity" in finding
            assert "dimension" in finding
            assert finding["dimension"] == "Security"
            assert "message" in finding
            assert "description" in finding

    def test_all_finding_ids_unique(self):
        tree = [
            {"path": ".gitignore"},
            {"path": ".env"},
            {"path": "id_rsa"},
            {"path": "SECURITY.md"},
            {"path": "package-lock.json"},
            {"path": ".github/dependabot.yml"},
            {"path": ".github/workflows/codeql-analysis.yml"},
        ]
        result = analyze_security(_make_input(tree=tree))
        ids = [f["id"] for f in result["findings"]]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 11. Dimension metadata
# ---------------------------------------------------------------------------

class TestDimensionMetadata:
    def test_returns_security_dimension(self):
        result = analyze_security(_make_input())
        assert result["id"] == "security"
        assert result["name"] == "Security"
        assert result["maxScore"] == 100
        assert result["weight"] == 15

    def test_confidence_is_string(self):
        result = analyze_security(_make_input())
        assert result["confidence"] in ("high", "medium", "low")

    def test_signals_list_populated(self):
        result = analyze_security(_make_input())
        assert len(result["signals"]) == 7

    def test_strengths_and_weaknesses_lists(self):
        tree = [{"path": ".gitignore"}, {"path": ".env"}]
        result = analyze_security(_make_input(tree=tree))
        assert isinstance(result["strengths"], list)
        assert isinstance(result["weaknesses"], list)
        assert len(result["strengths"]) > 0  # at least gitignore
        assert len(result["weaknesses"]) > 0  # env tracked

    def test_limitations_always_present(self):
        result = analyze_security(_make_input())
        assert len(result["limitations"]) > 0


# ---------------------------------------------------------------------------
# 12. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_tree(self):
        result = analyze_security(_make_input(tree=[]))
        assert result["score"] >= 0
        assert isinstance(result["findings"], list)

    def test_no_env_files_not_false_positive(self):
        """Other file types should not trigger env detection."""
        tree = [{"path": "README.md"}, {"path": "main.py"}]
        result = analyze_security(_make_input(tree=tree))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_tracked_env"]["status"] == "PRESENT"

    def test_nested_env_path_still_detected(self):
        """Regex match for .env.* should work for nested paths too."""
        # The regex is r'^\.env\.' which matches from start of path
        result = analyze_security(_make_input(
            tree=[{"path": ".env.staging"}],
        ))
        signals = {s["signal"]: s for s in result["signals"]}
        assert signals["no_tracked_env"]["status"] == "ABSENT"

    def test_simultaneous_critical_findings(self):
        """Both env and key exposure should produce separate critical findings."""
        tree = [{"path": ".env"}, {"path": "id_rsa"}]
        result = analyze_security(_make_input(tree=tree))
        critical = [f for f in result["findings"] if f["severity"] == "critical"]
        assert len(critical) == 2
        critical_ids = {f["id"] for f in critical}
        assert "sec-env" in critical_ids
        assert "sec-keys" in critical_ids

    def test_higher_security_score_with_more_positive_signals(self):
        """Adding more positive signals should increase the score."""
        tree_basic = [{"path": ".env"}]
        tree_hardened = [
            {"path": ".gitignore"},
            {"path": "package-lock.json"},
            {"path": "SECURITY.md"},
            {"path": ".github/dependabot.yml"},
            {"path": ".github/workflows/codeql-analysis.yml"},
        ]
        score_basic = analyze_security(_make_input(tree=tree_basic))["score"]
        score_hardened = analyze_security(_make_input(tree=tree_hardened))["score"]
        assert score_hardened > score_basic


# ---------------------------------------------------------------------------
# 13. Integration with create_finding / create_dimension helpers
# ---------------------------------------------------------------------------

class TestHelperIntegration:
    def test_create_finding_returns_dict(self):
        f = create_finding("test-id", "warning", "Security", "msg", "desc")
        assert f["id"] == "test-id"
        assert f["severity"] == "warning"
        assert f["dimension"] == "Security"

    def test_create_dimension_status_mapping(self):
        """Verify create_dimension maps scores to the right status labels."""
        test_cases = [
            (95, "exceptional"), (85, "strong"), (75, "good"),
            (65, "fair"), (45, "needs_work"), (20, "weak"),
        ]
        for score, expected_status in test_cases:
            dim = create_dimension(
                "security", "Security", score, 100, 15,
                [], [], "summary", "rec", {}, [], [], "high", "reason",
            )
            assert dim["status"] == expected_status, (
                f"Score {score} should map to status '{expected_status}'"
            )
