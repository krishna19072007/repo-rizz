import re
import math

def calculate_confidence(evidence_length: int, base_confidence: bool, limitations_length: int) -> str:
    if not base_confidence: return "low"
    if limitations_length > 2: return "low"
    if limitations_length > 0 or evidence_length < 5: return "medium"
    return "high"

def create_finding(id: str, severity: str, dimension: str, message: str, description: str, files=None, snippet=None, recommendation=None):
    return {
        "id": id,
        "severity": severity,
        "dimension": dimension,
        "message": message,
        "description": description,
        "files": files or [],
        "snippet": snippet,
        "recommendation": recommendation
    }

def create_dimension(dimension, dimensionName, score, maxScore, weight, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason):
    return {
        "id": dimension,
        "name": dimensionName,
        "score": score,
        "maxScore": maxScore,
        "weight": weight,
        "findings": findings,
        "evidence": evidence,
        "summary": summary,
        "recommendation": recommendation,
        "rawMetrics": rawMetrics,
        "rulesApplied": rulesApplied,
        "limitations": limitations,
        "confidence": confidence,
        "confidenceReason": confidenceReason
    }

def analyze_architecture(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = ["Architecture analysis inferred from directory structure — not from code inspection"]
    rawMetrics = {}
    
    tree = input_data.get("tree", [])
    checks = []
    
    frontend_files = [t for t in tree if any(t.get("path", "").startswith(p) for p in ["src/components/", "components/", "src/pages/", "pages/", "src/app/", "app/"])]
    has_frontend = len(frontend_files) > 2
    frontend_points = 15 if has_frontend else (5 if len(frontend_files) > 0 else 0)
    checks.append({
        "id": "frontend", "label": "Frontend structure", "points": frontend_points, "detected": len(frontend_files) > 0,
        "evidence": f"Frontend structure with {len(frontend_files)} files detected" if has_frontend else ("Minimal frontend structure detected" if len(frontend_files) > 0 else "No frontend structure detected")
    })
    
    backend_files = [t for t in tree if any(t.get("path", "").startswith(p) for p in ["src/api/", "api/", "server/", "src/server/", "routes/", "src/routes/"])]
    has_backend = len(backend_files) > 2
    backend_points = 15 if has_backend else (5 if len(backend_files) > 0 else 0)
    checks.append({
        "id": "backend", "label": "Backend/API structure", "points": backend_points, "detected": len(backend_files) > 0,
        "evidence": f"Backend/API structure with {len(backend_files)} files detected" if has_backend else ("Minimal backend structure detected" if len(backend_files) > 0 else "No backend structure detected")
    })
    
    service_files = [t for t in tree if any(t.get("path", "").startswith(p) for p in ["services/", "src/services/", "lib/", "src/lib/", "utils/", "src/utils/"])]
    has_services = len(service_files) > 2
    service_points = 10 if has_services else (3 if len(service_files) > 0 else 0)
    checks.append({
        "id": "services", "label": "Services/lib layer", "points": service_points, "detected": len(service_files) > 0,
        "evidence": f"Services/lib layer with {len(service_files)} files detected" if has_services else ("Minimal services layer detected" if len(service_files) > 0 else "No services layer detected")
    })
    
    build_configs = ["tsconfig.json", "next.config.js", "next.config.mjs", "next.config.ts", "vite.config.ts", "vite.config.js", "webpack.config.js", "rollup.config.js", "turbo.json", "nx.json"]
    has_build = any(any(t.get("path") == c for t in tree) for c in build_configs)
    checks.append({
        "id": "build", "label": "Build configuration", "points": 10, "detected": has_build,
        "evidence": "Build configuration detected" if has_build else "No build configuration found"
    })
    
    deploy_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "vercel.json", "netlify.toml", "fly.toml", "render.yaml", "Procfile"]
    has_deploy = any(any(t.get("path") == d for t in tree) for d in deploy_files)
    has_deploy_ci = any(t.get("path", "").startswith(".github/workflows/") and any(x in t.get("path", "") for x in ["deploy", "release", "publish"]) for t in tree)
    checks.append({
        "id": "deploy", "label": "Deployment configuration", "points": 15, "detected": has_deploy or has_deploy_ci,
        "evidence": "Deployment configuration found" if has_deploy else ("Deploy workflow detected" if has_deploy_ci else "No deployment configuration")
    })
    
    entry_points = ["index.ts", "index.js", "main.ts", "main.js", "server.ts", "app.ts", "src/index.ts", "src/main.ts", "src/server.ts"]
    has_entry = any(any(t.get("path") == e for t in tree) for e in entry_points)
    checks.append({
        "id": "entry", "label": "Clear entry point", "points": 10, "detected": has_entry,
        "evidence": "Clear entry point detected" if has_entry else "No standard entry point found"
    })
    
    has_db = any(any(x in t.get("path", "") for x in ["prisma/", "drizzle/", "migrations/", "schema.sql", "database."]) for t in tree)
    checks.append({
        "id": "database", "label": "Database/ORM layer", "points": 10, "detected": has_db,
        "evidence": "Database/ORM layer detected" if has_db else "No database layer detected"
    })
    
    has_config_dir = any(any(t.get("path", "").startswith(x) for x in ["config/", "src/config/", ".env.example"]) or t.get("path") in ["config.ts", "config.js"] for t in tree)
    checks.append({
        "id": "config", "label": "Configuration separation", "points": 5, "detected": has_config_dir,
        "evidence": "Configuration separation detected" if has_config_dir else "No config separation"
    })
    
    has_docs = any(t.get("path", "").startswith("docs/") for t in tree)
    checks.append({
        "id": "docs", "label": "Documentation directory", "points": 5, "detected": has_docs,
        "evidence": "docs/ directory present" if has_docs else "No docs/ directory"
    })
    
    total_points = sum(c["points"] for c in checks)
    earned_points = sum(c["points"] for c in checks if c["detected"])
    max_score = 100
    score = round((earned_points / total_points) * max_score) if total_points > 0 else 0
    
    for check in checks:
        rulesApplied.append(f"{check['id']} = +{check['points'] if check['detected'] else 0}")
        evidence.append(f"✓ {check['label']}: {check['evidence']}" if check["detected"] else f"✗ {check['label']}: {check['evidence']}")
        if check["detected"]:
            findings.append(create_finding(f"arch-{check['id']}", "positive", "Architecture", check['label'], check['evidence']))
            
    rawMetrics.update({
        "hasFrontend": has_frontend,
        "hasBackend": has_backend,
        "hasServices": has_services,
        "hasBuild": has_build,
        "hasDeploy": has_deploy or has_deploy_ci,
        "hasEntry": has_entry,
        "hasDb": has_db,
        "hasConfig": has_config_dir,
        "hasDocs": has_docs
    })
    
    confidence = calculate_confidence(len(evidence), True, len(limitations))
    confidenceReason = "Architecture inferred from directory structure — not from code inspection"
    
    if score >= 80: summary = "Well-organized architecture."
    elif score >= 60: summary = "Good structure with some gaps."
    elif score >= 40: summary = "Basic structure present."
    else: summary = "Architecture needs better organization."
    
    recommendation = "Maintain clean separation of concerns." if score >= 70 else "Add clear directory structure with separation between frontend, backend, and services."
    
    return create_dimension("architecture", "Architecture", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason)


def analyze_code_quality(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = ["Deep static analysis (AST parsing, complexity metrics) not included — analysis limited to file-level signals"]
    rawMetrics = {}
    
    tree = input_data.get("tree", [])
    checks = []
    
    lint_configs = [".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", "biome.json", ".stylelintrc", "stylelint.config.js", ".flake8", "ruff.toml", ".pylintrc", ".golangci.yml", "golangci.yml", ".golangci.json", ".golangci.toml", "clippy.toml", "checkstyle.xml", "pmd.xml", "spotbugs.xml", ".rubocop.yml", ".pre-commit-config.yaml"]
    has_lint = any(any(t.get("path", "") == c or t.get("path", "").endswith(f"/{c}") for t in tree) for c in lint_configs)
    checks.append({"id": "lint", "label": "Linting configuration", "points": 15, "detected": has_lint, "evidence": "Linting configuration detected" if has_lint else "No linting configuration found"})
    
    format_configs = [".prettierrc", ".prettierrc.js", ".prettierrc.json", "prettier.config.js", ".editorconfig", "biome.json", "black.toml", ".isort.cfg", "rustfmt.toml"]
    has_format = any(any(t.get("path", "") == c or t.get("path", "").endswith(f"/{c}") for t in tree) for c in format_configs)
    checks.append({"id": "format", "label": "Formatting configuration", "points": 10, "detected": has_format, "evidence": "Code formatting configuration detected" if has_format else "No formatting configuration found"})
    
    ecosystem_configs = ["tsconfig.json", "jsconfig.json", "mypy.ini", "pyproject.toml", "requirements.txt", "Pipfile", "go.mod", "Cargo.toml", "build.gradle", "pom.xml", "build.sbt", "Gemfile"]
    has_typing_ecosystem = any(any(t.get("path", "") == c or t.get("path", "").endswith(f"/{c}") for t in tree) for c in ecosystem_configs)
    checks.append({"id": "ecosystem", "label": "Ecosystem configuration", "points": 10, "detected": has_typing_ecosystem, "evidence": "Ecosystem/typing configuration detected" if has_typing_ecosystem else "No ecosystem configuration"})
    
    src_dirs = ["src/", "app/", "pages/", "components/", "lib/", "server/", "api/", "backend/", "frontend/", "pkg/", "cmd/", "internal/"]
    has_structure = any(any(t.get("path", "").startswith(d) for t in tree) for d in src_dirs)
    checks.append({"id": "structure", "label": "Organized directory structure", "points": 10, "detected": has_structure, "evidence": "Organized source directory structure detected" if has_structure else "Flat or unstructured layout"})
    
    source_exts = [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".rb", ".php", ".cs", ".cpp", ".c", ".h"]
    source_files = [t for t in tree if any(t.get("path", "").endswith(ext) for ext in source_exts)]
    test_regex = re.compile(r'\.(test|spec)\.(tsx?|jsx?|ts|js|py|go|rs|java|rb|php|cs|cpp|c|h)$')
    test_files = [t for t in tree if test_regex.search(t.get("path", "")) or "__tests__" in t.get("path", "") or t.get("path", "").startswith("tests/") or t.get("path", "").startswith("test/")]
    test_ratio = len(test_files) / len(source_files) if source_files else 0
    has_good_ratio = test_ratio > 0.1
    checks.append({"id": "test_ratio", "label": "Test-to-source ratio", "points": 10, "detected": has_good_ratio, "evidence": f"Test ratio: {int(test_ratio * 100)}% ({len(test_files)}/{len(source_files)})" if has_good_ratio else f"Low test ratio: {int(test_ratio * 100)}%"})
    
    script_score = 0
    task_tools = []
    package_json = input_data.get("packageJson")
    if package_json:
        scripts = package_json.get("scripts")
        if isinstance(scripts, dict):
            keys = list(scripts.keys())
            if len(keys) >= 5: script_score += 5
            if any(any(x in k for x in ["lint", "format", "typecheck", "test", "build"]) for k in keys): script_score += 5
            task_tools.append("package.json scripts")
            
    other_task_runners = ["Makefile", "justfile", "tox.ini", "Taskfile.yml", "Taskfile.yaml"]
    if any(any(t.get("path") == c for t in tree) for c in other_task_runners):
        script_score = 10
        task_tools.append("Task runner")
        
    has_good_scripts = script_score >= 5
    checks.append({"id": "scripts", "label": "Task runners & scripts", "points": 10, "detected": has_good_scripts, "evidence": f"Task tooling detected ({', '.join(task_tools)})" if has_good_scripts else "Limited or no task automation"})
    
    languages = list(input_data.get("languages", {}).keys())
    is_polyglot = len(languages) > 1
    checks.append({"id": "polyglot", "label": "Multiple languages", "points": 5, "detected": is_polyglot, "evidence": f"{len(languages)} languages detected" if is_polyglot else "Single language project"})
    
    large_files = [t for t in tree if t.get("size", 0) > 500000]
    if len(large_files) > 3:
        findings.append(create_finding("cq-large", "warning", "Code Quality", "Many large files", f"{len(large_files)} files over 500KB", [f.get("path") for f in large_files[:3]], large_files[0].get("path") if large_files else None, "Consider using git-lfs for large binary files."))
        
    total_points = sum(c["points"] for c in checks)
    earned_points = sum(c["points"] for c in checks if c["detected"])
    max_score = 100
    score = round((earned_points / total_points) * max_score) if total_points > 0 else 0
    
    for check in checks:
        rulesApplied.append(f"{check['id']} = +{check['points'] if check['detected'] else 0}")
        evidence.append(f"✓ {check['label']}: {check['evidence']}" if check["detected"] else f"✗ {check['label']}: {check['evidence']}")
        if check["detected"]:
            findings.append(create_finding(f"cq-{check['id']}", "positive", "Code Quality", check['label'], check['evidence']))
            
    rawMetrics.update({
        "hasLint": has_lint, "hasFormat": has_format, "hasTs": has_typing_ecosystem, "hasStructure": has_structure,
        "testRatio": test_ratio, "scriptScore": script_score, "languageCount": len(languages), "sourceFileCount": len(source_files), "testFileCount": len(test_files)
    })
    
    confidence = calculate_confidence(len(evidence), True, len(limitations))
    confidenceReason = "Code quality analysis limited to file-level signals — no AST analysis"
    
    if score >= 80: summary = "Strong code quality tooling."
    elif score >= 60: summary = "Good quality tooling with gaps."
    elif score >= 40: summary = "Basic quality tooling."
    else: summary = "Code quality tooling needs work."
    
    recommendation = "Maintain current standards." if score >= 70 else "Add linting, formatting, and ecosystem configuration."
    
    return create_dimension("codeQuality", "Code Quality", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason)


def get_section_depth(markdown: str, keyword_regex: re.Pattern) -> int:
    lines = markdown.split('\n')
    in_section = False
    section_lines = 0
    for line in lines:
        is_heading = re.match(r'^#{1,6}\s', line)
        if is_heading:
            if keyword_regex.search(line):
                in_section = True
                continue
            elif in_section:
                break
        if in_section and len(line.strip()) > 0:
            section_lines += 1
    return section_lines

def analyze_documentation(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = []
    rawMetrics = {}
    
    tree = input_data.get("tree", [])
    readme = input_data.get("readme", "")
    checks = []
    
    has_readme = bool(readme)
    checks.append({"id": "readme_exists", "label": "README exists", "points": 10, "detected": has_readme, "evidence": "README.md found in repository" if has_readme else "No README.md found"})
    if not has_readme:
        findings.append(create_finding("doc-no-readme", "critical", "Documentation", "No README found", "Repository has no README.md file.", [], None, "Create a comprehensive README.md with project description, installation, usage, and contribution instructions."))
        
    has_description = False
    if readme:
        lines = [l for l in readme.split('\n') if l.strip()]
        has_description = any(not l.startswith("#") and len(l.strip()) > 20 for l in lines)
    checks.append({"id": "description", "label": "Project description", "points": 10, "detected": has_description, "evidence": "Project description found in README" if has_description else "No meaningful description found"})
    
    has_install = False
    install_points = 0
    if readme:
        install_regex = re.compile(r'install|setup|getting.started|quick.start', re.IGNORECASE)
        has_install = bool(install_regex.search(readme))
        depth = get_section_depth(readme, install_regex)
        install_points = 15 if depth > 5 else 5 if has_install else 0
    checks.append({"id": "installation", "label": "Installation/setup instructions", "points": install_points, "detected": has_install, "evidence": "Detailed installation instructions found" if install_points == 15 else ("Brief installation instructions found" if has_install else "No installation instructions found")})
    
    has_usage = False
    usage_points = 0
    if readme:
        usage_regex = re.compile(r'usage|how.to.use|quick.start|commands', re.IGNORECASE)
        has_usage = bool(usage_regex.search(readme))
        depth = get_section_depth(readme, usage_regex)
        usage_points = 15 if depth > 5 else 5 if has_usage else 0
    checks.append({"id": "usage", "label": "Usage instructions", "points": usage_points, "detected": has_usage, "evidence": "Detailed usage instructions found" if usage_points == 15 else ("Brief usage instructions found" if has_usage else "No usage instructions found")})
    
    has_examples = False
    example_points = 0
    if readme:
        example_regex = re.compile(r'example|demo|sample|snippet', re.IGNORECASE)
        has_examples = bool(example_regex.search(readme))
        depth = get_section_depth(readme, example_regex)
        example_points = 10 if depth > 3 else 3 if has_examples else 0
    checks.append({"id": "examples", "label": "Examples", "points": example_points, "detected": has_examples, "evidence": "Detailed examples/demos found" if example_points == 10 else ("Brief examples found" if has_examples else "No examples found")})
    
    has_config_docs = False
    if readme: has_config_docs = bool(re.search(r'config|environment|env|\.env|variable|option', readme, re.IGNORECASE))
    checks.append({"id": "config_docs", "label": "Configuration documentation", "points": 10, "detected": has_config_docs, "evidence": "Configuration documentation found" if has_config_docs else "No configuration documentation found"})
    
    has_arch_docs = False
    if readme: has_arch_docs = bool(re.search(r'architecture|design|overview|api|endpoint|interface', readme, re.IGNORECASE))
    has_docs_dir = any(t.get("path", "").startswith("docs/") for t in tree)
    checks.append({"id": "architecture_docs", "label": "Architecture/API documentation", "points": 10, "detected": has_arch_docs or has_docs_dir, "evidence": "Architecture or API documentation found in README" if has_arch_docs else ("docs/ directory present" if has_docs_dir else "No architecture documentation found")})
    
    has_license = bool(input_data.get("license"))
    checks.append({"id": "license", "label": "License file", "points": 10, "detected": has_license, "evidence": "LICENSE file present" if has_license else "No LICENSE file found"})
    if not has_license: findings.append(create_finding("doc-no-license", "warning", "Documentation", "No LICENSE file found", "Repository lacks a license file.", [], None, "Add a LICENSE file to clarify usage rights."))
    
    has_contributing = bool(input_data.get("contributing"))
    checks.append({"id": "contributing", "label": "Contribution guide", "points": 5, "detected": has_contributing, "evidence": "CONTRIBUTING guide found" if has_contributing else "No contribution guide found"})
    
    has_security = bool(input_data.get("security"))
    checks.append({"id": "security_doc", "label": "Security documentation", "points": 5, "detected": has_security, "evidence": "SECURITY documentation found" if has_security else "No security documentation found"})
    
    has_changelog = bool(input_data.get("changelog"))
    checks.append({"id": "changelog", "label": "Changelog", "points": 5, "detected": has_changelog, "evidence": "CHANGELOG found" if has_changelog else "No changelog found"})
    
    has_codeowners = bool(input_data.get("codeowners"))
    checks.append({"id": "codeowners", "label": "CODEOWNERS", "points": 3, "detected": has_codeowners, "evidence": "CODEOWNERS present" if has_codeowners else "No CODEOWNERS found"})
    
    has_templates = any(t.get("path", "").startswith(".github/ISSUE_TEMPLATE") or t.get("path", "").startswith(".github/PULL_REQUEST_TEMPLATE") for t in tree)
    checks.append({"id": "templates", "label": "Issue/PR templates", "points": 4, "detected": has_templates, "evidence": "Issue/PR templates detected" if has_templates else "No issue/PR templates found"})
    
    has_screenshots = False
    if readme: has_screenshots = bool(re.search(r'screenshot|image|gif|demo|video|preview', readme, re.IGNORECASE) and re.search(r'!\[.*\]\(.*\)', readme, re.IGNORECASE))
    checks.append({"id": "screenshots", "label": "Visual assets in README", "points": 3, "detected": has_screenshots, "evidence": "Screenshots or visual assets found in README" if has_screenshots else "No visual assets detected"})
    
    total_points = sum(c["points"] for c in checks)
    earned_points = sum(c["points"] for c in checks if c["detected"])
    max_score = 100
    score = round((earned_points / total_points) * max_score) if total_points > 0 else 0
    
    for check in checks:
        rulesApplied.append(f"{check['id']} = +{check['points'] if check['detected'] else 0}")
        evidence.append(f"✓ {check['label']}: {check['evidence']}" if check["detected"] else f"✗ {check['label']}: {check['evidence']}")
        if check["detected"]: findings.append(create_finding(f"doc-{check['id']}", "positive", "Documentation", check['label'], check['evidence']))
        
    rawMetrics.update({
        "hasReadme": has_readme, "hasDescription": has_description, "hasInstall": has_install, "hasUsage": has_usage,
        "hasExamples": has_examples, "hasConfigDocs": has_config_docs, "hasArchDocs": has_arch_docs or has_docs_dir,
        "hasLicense": has_license, "hasContributing": has_contributing, "hasSecurityDoc": has_security,
        "hasChangelog": has_changelog, "hasCodeowners": has_codeowners, "hasTemplates": has_templates, "hasScreenshots": has_screenshots,
        "readmeLength": len(readme) if readme else 0
    })
    
    if not readme: limitations.append("README content not available for analysis")
    confidence = calculate_confidence(len(evidence), bool(readme), len(limitations))
    confidenceReason = "README not available — limited documentation analysis" if not readme else ("Comprehensive documentation evidence available" if len(evidence) >= 10 else "Partial documentation evidence available")
    
    if score >= 80: summary = "Excellent documentation coverage."
    elif score >= 60: summary = "Good documentation with room for improvement."
    elif score >= 40: summary = "Basic documentation exists but is incomplete."
    else: summary = "Documentation needs significant work."
    
    if score >= 80: recommendation = "Keep documentation updated with code changes."
    elif score >= 60: recommendation = "Add missing sections to improve completeness."
    else: recommendation = "Improve README with installation, usage, examples, and architecture sections."
    
    return create_dimension("documentation", "Documentation", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason)


def analyze_security(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = []
    rawMetrics = {}
    
    tree = input_data.get("tree", [])
    checks = []
    
    has_security_md = bool(input_data.get("security"))
    security_md_points = 15 if (has_security_md and len(input_data.get("security", "")) > 100) else (5 if has_security_md else 0)
    checks.append({"id": "security_md", "label": "SECURITY.md", "points": security_md_points, "detected": has_security_md, "evidence": "Detailed SECURITY.md found" if security_md_points == 15 else ("Brief SECURITY.md found" if has_security_md else "No SECURITY.md found")})
    
    env_files = [t for t in tree if t.get("path") in [".env", ".env.local", ".env.production", ".env.development"] or re.match(r'^\.env\.', t.get("path", ""))]
    has_tracked_env = len(env_files) > 0
    if has_tracked_env:
        findings.append(create_finding("sec-env", "critical", "Security", "Environment files tracked in repository", "Found .env files that may contain secrets.", [f.get("path") for f in env_files], env_files[0].get("path") if env_files else None, "Add .env files to .gitignore immediately and rotate any exposed secrets."))
        evidence.append(f"✗ .env files tracked: {', '.join(f.get('path') for f in env_files)}")
        rulesApplied.append("tracked_env = -20")
        
    has_gitignore = any(t.get("path") == ".gitignore" for t in tree)
    checks.append({"id": "gitignore", "label": ".gitignore", "points": 10, "detected": has_gitignore, "evidence": ".gitignore present" if has_gitignore else "No .gitignore found"})
    
    has_dependabot = any(t.get("path") in [".github/dependabot.yml", ".github/dependabot.yaml"] for t in tree)
    checks.append({"id": "dependabot", "label": "Dependabot", "points": 10, "detected": has_dependabot, "evidence": "Dependabot configuration detected" if has_dependabot else "No Dependabot configuration"})
    
    security_workflows = [t for t in tree if t.get("path", "").startswith(".github/workflows/") and any(x in t.get("path", "").lower() for x in ["security", "codeql", "snyk", "trivy"])]
    checks.append({"id": "security_ci", "label": "Security CI workflow", "points": 10, "detected": len(security_workflows) > 0, "evidence": f"{len(security_workflows)} security workflow(s) detected" if len(security_workflows) > 0 else "No security CI workflows"})
    
    key_patterns = [re.compile(r'\.pem$'), re.compile(r'\.key$'), re.compile(r'\.p12$'), re.compile(r'\.pfx$'), re.compile(r'\.jks$'), re.compile(r'id_rsa'), re.compile(r'id_ed25519'), re.compile(r'id_dsa'), re.compile(r'id_ecdsa'), re.compile(r'\.keystore$')]
    key_files = [t for t in tree if any(p.search(t.get("path", "")) for p in key_patterns)]
    if key_files:
        findings.append(create_finding("sec-keys", "critical", "Security", "Private key files detected", f"{len(key_files)} private key file(s) found in repository.", [f.get("path") for f in key_files], key_files[0].get("path") if key_files else None, "Remove private keys from the repository and add them to .gitignore."))
        evidence.append(f"✗ Private key files: {', '.join(f.get('path') for f in key_files)}")
        rulesApplied.append("private_keys = -15")
        
    lock_files = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum"]
    has_lock = any(any(t.get("path") == l for t in tree) for l in lock_files)
    checks.append({"id": "lockfile", "label": "Dependency lock file", "points": 5, "detected": has_lock, "evidence": "Dependency lock file present" if has_lock else "No lock file found"})
    
    security_libs = ["helmet", "cors", "csurf", "bcrypt", "dompurify", "jsonwebtoken"]
    has_sec_libs = False
    pkg = input_data.get("packageJson", {})
    if pkg and (pkg.get("dependencies") or pkg.get("devDependencies")):
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        has_sec_libs = any(lib in deps for lib in security_libs)
    checks.append({"id": "security_libs", "label": "Security libraries", "points": 5, "detected": has_sec_libs, "evidence": "Security libraries/middleware detected" if has_sec_libs else "No obvious security libraries found"})
    
    has_dockerfile = any(t.get("path") == "Dockerfile" for t in tree)
    has_dockerignore = any(t.get("path") == ".dockerignore" for t in tree)
    if has_dockerfile and not has_dockerignore:
        findings.append(create_finding("sec-docker", "info", "Security", "Docker without .dockerignore", "Dockerfile found but no .dockerignore.", [], "Dockerfile", "Add .dockerignore to prevent sensitive files in Docker builds."))
        
    total_points = sum(c["points"] for c in checks)
    earned_from_checks = sum(c["points"] for c in checks if c["detected"])
    penalty_points = (-20 if has_tracked_env else 0) + (-15 if len(key_files) > 0 else 0)
    max_score = 100
    raw_score = round((earned_from_checks / total_points) * 100) if total_points > 0 else 0
    score = max(0, min(max_score, raw_score + penalty_points))
    
    for check in checks:
        rulesApplied.append(f"{check['id']} = +{check['points'] if check['detected'] else 0}")
        evidence.append(f"✓ {check['label']}: {check['evidence']}" if check["detected"] else f"✗ {check['label']}: {check['evidence']}")
        if check["detected"]: findings.append(create_finding(f"sec-{check['id']}", "positive", "Security", check['label'], check['evidence']))
        
    rawMetrics.update({
        "hasSecurityMd": has_security_md, "hasTrackedEnv": has_tracked_env, "envFileCount": len(env_files),
        "hasGitignore": has_gitignore, "hasDependabot": has_dependabot, "securityWorkflowCount": len(security_workflows),
        "keyFileCount": len(key_files), "hasLock": has_lock, "hasDockerfile": has_dockerfile
    })
    
    limitations.append("Deep vulnerability scanning (SAST/DAST) not included — analysis limited to file-level signals")
    confidence = calculate_confidence(len(evidence), True, len(limitations))
    confidenceReason = "Critical security issues detected with high confidence" if has_tracked_env or len(key_files) > 0 else "Security analysis based on file presence — deep vulnerability scanning not included"
    
    if score >= 80: summary = "Strong security practices detected."
    elif score >= 60: summary = "Good security posture with minor gaps."
    elif score >= 40: summary = "Some security measures but significant gaps."
    else: summary = "Security needs significant attention."
    
    recommendation = "Maintain security practices and consider adding automated security scanning." if score >= 80 else "Address critical security findings and add security documentation."
    
    return create_dimension("security", "Security", score, max_score, 15, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason)


def analyze_testing(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = []
    rawMetrics = {}
    
    tree = input_data.get("tree", [])
    checks = []
    
    test_file_patterns = [
        re.compile(r'\.(test|spec)\.(tsx?|jsx?|ts|js)$'), re.compile(r'\.(test|spec)\.(py|go|rs|java|rb)$'),
        re.compile(r'__tests__'), re.compile(r'^tests?/'), re.compile(r'^spec/'), re.compile(r'\btest_', re.IGNORECASE), re.compile(r'_test\.', re.IGNORECASE)
    ]
    test_files = [t for t in tree if any(p.search(t.get("path", "")) for p in test_file_patterns)]
    test_file_count = len(set(f.get("path") for f in test_files))
    has_test_files = test_file_count > 0
    checks.append({"id": "test_files", "label": "Test files", "points": 25, "detected": has_test_files, "evidence": f"{test_file_count} test file(s) detected" if has_test_files else "No test files detected in inspected tree"})
    
    framework_configs = {
        "Jest": ["jest.config.js", "jest.config.ts", "jest.config.mjs", "jest.config.cjs"],
        "Vitest": ["vitest.config.ts", "vitest.config.js", "vitest.config.mjs"],
        "Mocha": [".mocharc.yml", ".mocharc.json", ".mocharc.js"],
        "Cypress": ["cypress.config.js", "cypress.config.ts", "cypress.json"],
        "Playwright": ["playwright.config.ts", "playwright.config.js"],
        "Karma": ["karma.conf.js", "karma.conf.cjs"]
    }
    
    detected_framework = ""
    for name, configs in framework_configs.items():
        if any(any(t.get("path") == c for t in tree) for c in configs):
            detected_framework = name
            break
            
    if not detected_framework and any(t.get("path") in ["pytest.ini", "setup.cfg", "pyproject.toml"] for t in tree):
        detected_framework = "pytest (config detected)"
    if not detected_framework and any(t.get("path") in ["pom.xml", "build.gradle", "build.gradle.kts"] for t in tree):
        detected_framework = "JUnit (Java project detected)"
    if not detected_framework and any(t.get("path") == "go.mod" for t in tree) and test_file_count > 0:
        detected_framework = "Go testing (built-in)"
    if not detected_framework and any(t.get("path") == "Cargo.toml" for t in tree) and test_file_count > 0:
        detected_framework = "Rust testing (built-in)"
        
    has_framework = bool(detected_framework)
    checks.append({"id": "test_framework", "label": "Test framework", "points": 20, "detected": has_framework, "evidence": f"Test framework detected: {detected_framework}" if has_framework else "No test framework configuration detected"})
    
    has_test_script = False
    test_script_name = ""
    pkg = input_data.get("packageJson", {})
    if pkg and isinstance(pkg.get("scripts"), dict):
        test_keys = [k for k in pkg.get("scripts", {}).keys() if k == "test" or "test" in k or "spec" in k]
        if test_keys:
            has_test_script = True
            test_script_name = test_keys[0]
    checks.append({"id": "test_script", "label": "Test script", "points": 15, "detected": has_test_script, "evidence": f'Test script found: "{test_script_name}"' if has_test_script else "No test script found in package.json"})
    
    ci_test_workflows = [t for t in tree if t.get("path", "").startswith(".github/workflows/") and any(x in t.get("path", "") for x in ["test", "ci", "check"])]
    has_ci_tests = len(ci_test_workflows) > 0
    checks.append({"id": "ci_tests", "label": "CI test execution", "points": 15, "detected": has_ci_tests, "evidence": f"{len(ci_test_workflows)} CI workflow(s) that may run tests" if has_ci_tests else "No CI test execution detected"})
    
    has_coverage = False
    if pkg and isinstance(pkg.get("scripts"), dict):
        has_coverage = any("coverage" in k or ("coverage" in (pkg["scripts"][k] or "")) for k in pkg.get("scripts", {}).keys())
    if not has_coverage:
        coverage_indicators = ["jest.config.js", "jest.config.ts", ".nycrc", ".nycrc.json", ".nycrc.yml", "vitest.config.ts", "vitest.config.js", "coverage/"]
        has_coverage = any(any(t.get("path") == c or t.get("path", "").startswith(c) for t in tree) for c in coverage_indicators)
    checks.append({"id": "coverage", "label": "Coverage configuration", "points": 10, "detected": has_coverage, "evidence": "Coverage configuration detected" if has_coverage else "No coverage configuration found"})
    
    test_helpers = [t for t in tree if any(x in t.get("path", "") for x in ["test-utils", "testUtils", "setupTests", "setup.tests", "test-setup", "testSetup", "test.helper", "testHelper"])]
    has_test_helpers = len(test_helpers) > 0
    checks.append({"id": "test_helpers", "label": "Test helper files", "points": 5, "detected": has_test_helpers, "evidence": "Test helper/utility files detected" if has_test_helpers else "No test helper files found"})
    
    e2e_frameworks = ["playwright", "cypress", "puppeteer", "selenium"]
    has_e2e = any(
        any(fw in t.get("path", "") for t in tree) or
        (fw in (pkg.get("dependencies", {}) if isinstance(pkg.get("dependencies"), dict) else {})) or
        (fw in (pkg.get("devDependencies", {}) if isinstance(pkg.get("devDependencies"), dict) else {}))
        for fw in e2e_frameworks
    )
    checks.append({"id": "e2e", "label": "E2E testing", "points": 10, "detected": has_e2e, "evidence": "E2E testing framework detected" if has_e2e else "No E2E testing detected"})
    
    total_points = sum(c["points"] for c in checks)
    earned_points = sum(c["points"] for c in checks if c["detected"])
    max_score = 100
    score = round((earned_points / total_points) * max_score) if total_points > 0 else 0
    
    for check in checks:
        rulesApplied.append(f"{check['id']} = +{check['points'] if check['detected'] else 0}")
        evidence.append(f"✓ {check['label']}: {check['evidence']}" if check["detected"] else f"✗ {check['label']}: {check['evidence']}")
        if check["detected"]: findings.append(create_finding(f"test-{check['id']}", "positive", "Testing", check['label'], check['evidence']))
        
    if not has_test_files and not has_framework:
        findings.append(create_finding("test-none", "critical", "Testing", "No testing infrastructure detected", "No test files, test directories, or test framework configuration found.", [], None, "Set up a testing framework (Jest, Vitest, Playwright) and add tests for core functionality."))
        
    rawMetrics.update({
        "testFileCount": test_file_count, "detectedFramework": detected_framework or "none", "hasTestScript": has_test_script,
        "hasCITests": has_ci_tests, "hasCoverage": has_coverage, "hasTestHelpers": has_test_helpers, "hasE2E": has_e2e
    })
    
    if test_file_count == 0: limitations.append("No test files found — analysis limited to configuration detection")
    confidence = calculate_confidence(len(evidence), test_file_count > 0 or has_framework, len(limitations))
    confidenceReason = "Test files found in repository — high confidence" if test_file_count > 0 else ("Test framework config found but no test files visible" if has_framework else "No testing evidence found — cannot confirm absence of tests in unindexed paths")
    
    if score >= 80: summary = "Strong testing infrastructure with good coverage."
    elif score >= 60: summary = "Testing infrastructure present but could be more comprehensive."
    elif score >= 40: summary = "Some testing evidence but significant gaps."
    elif score >= 20: summary = "Minimal testing infrastructure detected."
    else: summary = "No testing infrastructure detected."
    
    if score >= 80: recommendation = "Maintain test coverage and add integration tests."
    elif score >= 60: recommendation = "Expand test coverage and add edge case tests."
    else: recommendation = "Set up a testing framework and add tests for critical functionality."
    
    return create_dimension("testing", "Testing", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason)
