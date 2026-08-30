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

def create_dimension(dimension, dimensionName, score, maxScore, weight, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason, strengths=None, weaknesses=None, applicableSignals=None, notApplicableSignals=None, signals=None):
    if score >= 90:
        status = "exceptional"
    elif score >= 80:
        status = "strong"
    elif score >= 70:
        status = "good"
    elif score >= 60:
        status = "fair"
    elif score >= 40:
        status = "needs_work"
    else:
        status = "weak"

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
        "confidenceReason": confidenceReason,
        "status": status,
        "strengths": strengths or [],
        "weaknesses": weaknesses or [],
        "applicableSignals": applicableSignals or [],
        "notApplicableSignals": notApplicableSignals or [],
        "signals": signals or []
    }

def analyze_architecture(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = ["Architecture analysis inferred from directory structure and file contents — not full AST parsing"]
    rawMetrics = {}
    
    classification = input_data.get("classification", {})
    repo_type = classification.get("type", "UNKNOWN")
    
    tree = input_data.get("tree", [])
    tree_paths = [t.get("path", "") for t in tree]
    
    important_files = input_data.get("importantFiles", {})
    package_json = input_data.get("packageJson")

    # 1. Recursive Backend Detection
    backend_indicators = ["main.py", "app.py", "server.js", "app.js", "index.js", "main.go", "app.ts", "server.ts"]
    backend_paths = []
    has_backend = False
    backend_evidence = []
    
    for item in tree:
        path = item.get("path", "")
        parts = path.split("/")
        if any(p in ["backend", "server", "api", "python-backend"] or "backend" in p or "server" in p or "api" in p for p in parts[:-1]):
            if parts[-1] in backend_indicators or parts[-1].endswith(".py") or parts[-1].endswith(".js") or parts[-1].endswith(".go") or parts[-1].endswith(".ts"):
                backend_paths.append(path)
                
    for item in tree:
        path = item.get("path", "")
        if path.endswith("main.py") or path.endswith("app.py") or path.endswith("app.js") or path.endswith("server.js"):
            if path not in backend_paths:
                backend_paths.append(path)
                
    fastapi_detected = False
    flask_detected = False
    django_detected = False
    
    for key, content in important_files.items():
        if "requirements.txt" in key or "pyproject.toml" in key or "Pipfile" in key:
            content_lower = content.lower()
            if "fastapi" in content_lower:
                fastapi_detected = True
                backend_evidence.append(f"FastAPI package found in {key}")
            if "flask" in content_lower:
                flask_detected = True
                backend_evidence.append(f"Flask package found in {key}")
            if "django" in content_lower:
                django_detected = True
                backend_evidence.append(f"Django package found in {key}")
                
    for key, content in important_files.items():
        if key.endswith("main.py") or key.endswith("app.py"):
            if "FastAPI(" in content or "fastapi" in content:
                fastapi_detected = True
                backend_evidence.append(f"FastAPI initialization found in {key}")
            if "Flask(__name__)" in content or "import flask" in content:
                flask_detected = True
                backend_evidence.append(f"Flask initialization found in {key}")
            if "django" in content:
                django_detected = True
                backend_evidence.append(f"Django import found in {key}")
                
    if backend_paths or backend_evidence:
        has_backend = True
        if backend_paths:
            backend_evidence.append(f"Backend files found: {', '.join(backend_paths[:3])}")
            
    # 2. Frontend Detection
    has_frontend = False
    frontend_evidence = []
    
    if package_json:
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        frontend_packages = ["next", "react", "vue", "svelte", "vite", "nuxt", "astro", "angular", "tailwind", "postcss"]
        detected_packages = [pkg for pkg in frontend_packages if pkg in deps]
        if detected_packages:
            frontend_evidence.append(f"Frontend packages in package.json: {', '.join(detected_packages)}")
            has_frontend = True
            
    frontend_dirs = ["src/components/", "components/", "src/pages/", "pages/", "src/app/", "app/", "frontend/", "public/"]
    matching_frontend_files = [t.get("path") for t in tree if any(t.get("path", "").startswith(d) for d in frontend_dirs)]
    if matching_frontend_files:
        frontend_evidence.append(f"UI directory files: {len(matching_frontend_files)} files detected")
        has_frontend = True
        
    frontend_configs = ["next.config.js", "next.config.mjs", "next.config.ts", "vite.config.ts", "vite.config.js", "tsconfig.json"]
    found_configs = [c for c in frontend_configs if any(t.get("path") == c for t in tree)]
    if found_configs:
        frontend_evidence.append(f"Config files: {', '.join(found_configs)}")
        has_frontend = True

    # 3. Integrations Detection
    has_github_int = False
    github_evidence = []
    if package_json:
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        if "@octokit/rest" in deps or "octokit" in deps:
            has_github_int = True
            github_evidence.append("GitHub client dependency in package.json")
            
    github_files = [t.get("path") for t in tree if "github.py" in t.get("path", "") or "github.ts" in t.get("path", "")]
    if github_files:
        has_github_int = True
        github_evidence.append(f"GitHub wrapper class file present: {github_files[0]}")
        
    for key, content in important_files.items():
        if "api.github.com" in content or "github_token" in content.lower():
            has_github_int = True
            github_evidence.append(f"GitHub API URL / token logic inside {key}")
            
    has_gemini_int = False
    gemini_evidence = []
    if package_json:
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        if "@google/genai" in deps or "@google/generative-ai" in deps:
            has_gemini_int = True
            gemini_evidence.append("Gemini JS client package in package.json")
            
    for key, content in important_files.items():
        if "google-generativeai" in content.lower() or "google-genai" in content.lower():
            has_gemini_int = True
            gemini_evidence.append(f"Gemini package listed in {key}")
        if "google.generativeai" in content or "google.genai" in content:
            if "import " in content:
                has_gemini_int = True
                gemini_evidence.append(f"Gemini client initialization in {key}")
                
    gemini_files = [t.get("path") for t in tree if "ai.py" in t.get("path", "").lower() or "ai.ts" in t.get("path", "").lower() or "gemini.py" in t.get("path", "").lower() or "gemini.ts" in t.get("path", "").lower()]
    if gemini_files:
        has_gemini_int = True
        gemini_evidence.append(f"AI/Gemini orchestration file present in tree: {gemini_files[0]}")

    has_supabase_int = False
    supabase_evidence = []
    if package_json:
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        if "@supabase/supabase-js" in deps or "supabase" in deps:
            has_supabase_int = True
            supabase_evidence.append("Supabase JS package in package.json")
            
    supabase_files = [t.get("path") for t in tree if t.get("path", "").startswith("supabase/")]
    if supabase_files:
        has_supabase_int = True
        supabase_evidence.append(f"Supabase schema/migration files found: {len(supabase_files)}")
        
    for key, content in important_files.items():
        if "supabase" in content.lower():
            has_supabase_int = True
            supabase_evidence.append(f"Supabase client initialization references inside {key}")

    # Structural Signals Evaluators
    has_services = any(any(t.get("path", "").startswith(p) for p in ["services/", "src/services/", "lib/", "src/lib/", "utils/", "src/utils/"]) for t in tree)
    service_files = [t for t in tree if any(t.get("path", "").startswith(p) for p in ["services/", "src/services/", "lib/", "src/lib/", "utils/", "src/utils/"])]
    
    build_configs = ["tsconfig.json", "next.config.js", "next.config.mjs", "next.config.ts", "vite.config.ts", "vite.config.js", "webpack.config.js", "pyproject.toml", "requirements.txt", "Cargo.toml", "go.mod"]
    has_build = any(any(t.get("path") == c for t in tree) for c in build_configs)
    
    deploy_files = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml", "vercel.json", "netlify.toml", "fly.toml"]
    has_deploy = any(any(t.get("path") == d for t in tree) for d in deploy_files) or any(t.get("path", "").startswith(".github/workflows/") and any(x in t.get("path", "") for x in ["deploy", "release", "publish"]) for t in tree)
    
    entry_points = ["index.ts", "index.js", "main.ts", "main.js", "server.ts", "app.ts", "src/index.ts", "src/main.ts", "src/server.ts", "index.py", "main.py", "app.py", "main.go"]
    has_entry = any(any(t.get("path") == e for t in tree) for e in entry_points)
    
    has_config_dir = any(any(t.get("path", "").startswith(x) for x in ["config/", "src/config/", ".env.example"]) or t.get("path") in ["config.ts", "config.js"] for t in tree)
    has_docs = any(t.get("path", "").startswith("docs/") for t in tree)
    has_pkg_structure = any(any(t.get("path", "").startswith(x) for x in ["src/", "lib/", "pkg/", "cmd/", "dist/"]) for t in tree)
    has_curated_structure = len([t for t in tree if t.get("path", "").endswith(".md")]) > 2
    
    is_frontend_only = has_frontend and not has_backend
    is_backend_only = has_backend and not has_frontend
    is_app = repo_type in ["APPLICATION", "UNKNOWN"]
    is_lib = repo_type in ["LIBRARY", "FRAMEWORK"]
    is_cli = repo_type == "CLI_TOOL"
    is_curated = repo_type in ["CURATED_LIST", "DOCUMENTATION", "DATASET", "EDUCATIONAL"]

    signals = []
    
    fe_applicable = is_app and not is_backend_only
    fe_status = "PRESENT" if has_frontend else "ABSENT"
    signals.append({
        "signal": "frontend_structure",
        "label": "Frontend components structure",
        "status": fe_status,
        "evidence": frontend_evidence or ["No frontend folders or dependencies found"],
        "applicability": "APPLICABLE" if fe_applicable else "NOT_APPLICABLE",
        "weight": 20,
        "reason": "Next.js/React layout or configurations detected" if has_frontend else "No frontend layout structures found"
    })
    
    be_applicable = is_app and not is_frontend_only
    be_status = "PRESENT" if has_backend else "ABSENT"
    signals.append({
        "signal": "backend_structure",
        "label": "Backend/API services structure",
        "status": be_status,
        "evidence": backend_evidence or ["No backend folders or code initialization found"],
        "applicability": "APPLICABLE" if be_applicable else "NOT_APPLICABLE",
        "weight": 20,
        "reason": "Python/FastAPI or Node.js backend entrypoint files detected" if has_backend else "No API route layouts found"
    })
    
    sep_applicable = is_app and not (is_frontend_only or is_backend_only)
    sep_status = "PRESENT" if (has_frontend and has_backend) else "ABSENT"
    signals.append({
        "signal": "separation_responsibilities",
        "label": "Separation of responsibilities",
        "status": sep_status,
        "evidence": [f"Frontend status: {fe_status}", f"Backend status: {be_status}"],
        "applicability": "APPLICABLE" if sep_applicable else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Frontend UI code is cleanly separated from backend API code" if (has_frontend and has_backend) else "Missing dual frontend/backend separation layers"
    })

    disc_status = "PRESENT" if has_entry else "ABSENT"
    signals.append({
        "signal": "discoverability",
        "label": "Entry points or public exports",
        "status": disc_status,
        "evidence": [f"Entry point file: {next((e for e in entry_points if any(t.get('path') == e for t in tree)), 'None')}" if has_entry else "No standard entry point found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Standard index, main or app routing entrypoint present" if has_entry else "Missing direct standard application entrypoints"
    })

    mod_status = "PRESENT" if has_services else "ABSENT"
    signals.append({
        "signal": "module_organization",
        "label": "Services/lib logic layers",
        "status": mod_status,
        "evidence": [f"{len(service_files)} helper module files in services/ or lib/ folders"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Dedicated logical modules for components and utility helpers found" if has_services else "Flat/unstructured logic directory structure"
    })

    config_status = "PRESENT" if has_config_dir else "ABSENT"
    signals.append({
        "signal": "configuration_separation",
        "label": "Separated configurations",
        "status": config_status,
        "evidence": ["Config files (.env.example or config/) detected" if has_config_dir else "No environment templates found"],
        "applicability": "APPLICABLE",
        "weight": 10,
        "reason": "Environment variables configuration templates or modules isolated" if has_config_dir else "Missing configuration folders or env files templates"
    })

    maint_status = "PRESENT" if has_build else "ABSENT"
    signals.append({
        "signal": "maintainability",
        "label": "Compiler or packaging configurations",
        "status": maint_status,
        "evidence": ["Ecosystem files found (package.json, tsconfig, requirements.txt, etc.)" if has_build else "No manifest configs"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Compiler configurations and package dependencies manifests present" if has_build else "Missing build or package config setups"
    })

    git_status = "PRESENT" if has_github_int else "ABSENT"
    signals.append({
        "signal": "github_integration",
        "label": "GitHub API integrations",
        "status": git_status,
        "evidence": github_evidence or ["No GitHub Octokit or API client references found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "GitHub SDK library client or API queries discovered" if has_github_int else "No GitHub API orchestration code references found"
    })

    gem_status = "PRESENT" if has_gemini_int else "ABSENT"
    signals.append({
        "signal": "gemini_integration",
        "label": "Gemini AI integrations",
        "status": gem_status,
        "evidence": gemini_evidence or ["No Google GenAI package or import references found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Google Gemini Generative AI SDK client integrations discovered" if has_gemini_int else "No AI generative orchestration code references found"
    })

    sb_status = "PRESENT" if has_supabase_int else "ABSENT"
    signals.append({
        "signal": "supabase_integration",
        "label": "Supabase integrations",
        "status": sb_status,
        "evidence": supabase_evidence or ["No Supabase package or config references found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Supabase database client queries or migration layouts discovered" if has_supabase_int else "No Supabase database code references found"
    })

    applicable_signals = []
    not_applicable_signals = []
    strengths = []
    weaknesses = []
    
    total_applicable_weight = 0
    earned_applicable_weight = 0
    
    for s in signals:
        rulesApplied.append(f"{s['signal']} = {'applicable' if s['applicability'] == 'APPLICABLE' else 'na'} (status: {s['status']})")
        if s["applicability"] == "APPLICABLE":
            total_applicable_weight += s["weight"]
            applicable_signals.append(s["label"])
            if s["status"] == "PRESENT":
                earned_applicable_weight += s["weight"]
                strengths.append(s["label"])
                evidence.append(f"✓ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"arch-{s['signal']}", "positive", "Architecture", s["label"], s["evidence"][0]))
            else:
                weaknesses.append(s["label"])
                evidence.append(f"✗ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"arch-{s['signal']}", "warning", "Architecture", f"Missing {s['label'].lower()}", f"{s['evidence'][0]} — applicable to this repository structure."))
        else:
            not_applicable_signals.append(s["label"])
            evidence.append(f"⊖ {s['label']} (N/A)")
            findings.append(create_finding(
                f"arch-{s['signal']}", 
                "info", 
                "Architecture", 
                f"{s['label']} not applicable", 
                f"This signal is not penalized because this repository classification type is {repo_type}."
            ))

    score = round((earned_applicable_weight / total_applicable_weight) * 100) if total_applicable_weight > 0 else 100
    
    rawMetrics.update({
        "hasFrontend": has_frontend,
        "hasBackend": has_backend,
        "hasServices": has_services,
        "hasBuild": has_build,
        "hasDeploy": has_deploy,
        "hasEntry": has_entry,
        "hasDb": has_supabase_int,
        "hasConfig": has_config_dir,
        "hasDocs": has_docs,
        "hasPkgStructure": has_pkg_structure,
        "hasCuratedStructure": has_curated_structure
    })
    
    if score >= 90: summary = "Exceptional architecture matching this repository type."
    elif score >= 80: summary = "Strong architecture structure with clear layer separation."
    elif score >= 70: summary = "Good architecture layout matching expected requirements."
    elif score >= 60: summary = "Fair structure layout containing minor organization gaps."
    elif score >= 40: summary = "Basic structure layout that needs separation of concerns."
    else: summary = "Architecture needs significant organization."
    
    if score >= 80:
        recommendation = "Maintain current architecture structure and code division standards."
    else:
        recommendation = "Refine repository organization by separating configurations, documentation, and source code."

    max_score = 100
    confidence = calculate_confidence(len(evidence), True, len(limitations))
    confidenceReason = "Architecture evaluation mapped to repository requirements recursively"
    return create_dimension("architecture", "Architecture", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason, strengths, weaknesses, applicable_signals, not_applicable_signals, signals)


def analyze_code_quality(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = ["Deep static analysis (AST parsing, complexity metrics) not included — analysis limited to file-level signals"]
    rawMetrics = {}
    
    classification = input_data.get("classification", {})
    repo_type = classification.get("type", "UNKNOWN")
    
    tree = input_data.get("tree", [])
    tree_paths = [t.get("path", "") for t in tree]
    important_files = input_data.get("importantFiles", {})
    package_json = input_data.get("packageJson")

    # Configuration Presence Detection
    has_lint_config = any(any(t.get("path", "") == c or t.get("path", "").endswith(f"/{c}") for t in tree) for c in [".eslintrc", ".eslintrc.js", ".eslintrc.json", ".eslintrc.yml", "eslint.config.js", "eslint.config.mjs", "eslint.config.cjs", "biome.json", ".stylelintrc", "stylelint.config.js", ".flake8", "ruff.toml", ".pylintrc", ".golangci.yml", "golangci.yml", "clippy.toml"])
    
    has_format_config = any(any(t.get("path", "") == c or t.get("path", "").endswith(f"/{c}") for t in tree) for c in [".prettierrc", ".prettierrc.js", ".prettierrc.json", "prettier.config.js", ".editorconfig", "biome.json", "black.toml", "rustfmt.toml"])
    
    has_typing_config = any(any(t.get("path", "") == c or t.get("path", "").endswith(f"/{c}") for t in tree) for c in ["tsconfig.json", "jsconfig.json", "mypy.ini", "pyproject.toml"])
    
    has_lint_usage = False
    has_format_usage = False
    has_automated_tasks = False
    task_tools = []
    
    if package_json:
        scripts = package_json.get("scripts", {})
        if isinstance(scripts, dict):
            if "lint" in scripts or any("eslint" in val for val in scripts.values()):
                has_lint_usage = True
            if "format" in scripts or any("prettier" in val for val in scripts.values()):
                has_format_usage = True
            if len(scripts) >= 3:
                has_automated_tasks = True
                task_tools.append("package.json scripts")
                
    other_task_runners = ["Makefile", "justfile", "tox.ini", "Taskfile.yml", "Taskfile.yaml"]
    if any(any(t.get("path") == c for t in tree) for c in other_task_runners):
        has_automated_tasks = True
        task_tools.append("Task runner (Makefile/justfile)")

    for key, content in important_files.items():
        if "pyproject.toml" in key or "requirements.txt" in key or "Pipfile" in key:
            content_lower = content.lower()
            if "black" in content_lower:
                has_format_config = True
                has_format_usage = True
            if "ruff" in content_lower or "flake8" in content_lower or "pylint" in content_lower:
                has_lint_config = True
                has_lint_usage = True
            if "pytest" in content_lower or "tox" in content_lower:
                has_automated_tasks = True
                
    lock_files = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum"]
    has_lockfile = any(any(t.get("path") == l for t in tree) for l in lock_files)
    
    languages = list(input_data.get("languages", {}).keys())
    is_polyglot = len(languages) > 1
    
    source_exts = [".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".rb", ".php", ".cs", ".cpp", ".c", ".h"]
    source_files = [t for t in tree if any(t.get("path", "").endswith(ext) for ext in source_exts)]
    
    test_regex = re.compile(r'\.(test|spec)\.(tsx?|jsx?|ts|js|py|go|rs|java|rb|php|cs|cpp|c|h)$')
    test_files = [t for t in tree if test_regex.search(t.get("path", "")) or "__tests__" in t.get("path", "") or t.get("path", "").startswith("tests/") or t.get("path", "").startswith("test/")]
    test_ratio = len(test_files) / len(source_files) if source_files else 0
    has_good_ratio = test_ratio > 0.03
    
    is_curated = repo_type in ["CURATED_LIST", "DOCUMENTATION", "DATASET", "EDUCATIONAL"]

    signals = []
    
    signals.append({
        "signal": "lint_config",
        "label": "Code linting configuration",
        "status": "PRESENT" if has_lint_config else "ABSENT",
        "evidence": ["Linter config file found (eslint, ruff, biome, etc.)" if has_lint_config else "No lint configuration files found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Linter settings/rules are configured" if has_lint_config else "Missing configuration parameters for linters"
    })
    
    signals.append({
        "signal": "lint_usage",
        "label": "Code linting usage",
        "status": "PRESENT" if has_lint_usage else "ABSENT",
        "evidence": ["Lint script configured in package.json/Makefile" if has_lint_usage else "No run target for linters found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Automated linting commands are wired to build cycles" if has_lint_usage else "Linter tool is not setup to run automated checks"
    })
    
    signals.append({
        "signal": "format_config",
        "label": "Code formatting style configuration",
        "status": "PRESENT" if has_format_config else "ABSENT",
        "evidence": ["Formatter config file found (prettier, black, etc.)" if has_format_config else "No formatting config files found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Formatting rules are explicitly declared" if has_format_config else "Formatting configuration is missing"
    })
    
    signals.append({
        "signal": "format_usage",
        "label": "Code formatting usage",
        "status": "PRESENT" if has_format_usage else "ABSENT",
        "evidence": ["Format run target detected in package.json/Makefile" if has_format_usage else "No formatter run scripts configured"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Source code formatting check command is configured" if has_format_usage else "No styling formatter trigger found in tasks list"
    })
    
    signals.append({
        "signal": "ecosystem_typing",
        "label": "Ecosystem typing configuration",
        "status": "PRESENT" if has_typing_config else "ABSENT",
        "evidence": ["Type configuration file found (tsconfig.json, mypy.ini, etc.)" if has_typing_config else "No typing configurations found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Strong typescript type compilation or python static type rules found" if has_typing_config else "Type annotations checking rules not present"
    })
    
    signals.append({
        "signal": "automated_tasks",
        "label": "Automated build & execution tasks",
        "status": "PRESENT" if has_automated_tasks else "ABSENT",
        "evidence": [f"Task automation configured via {', '.join(task_tools)}" if has_automated_tasks else "No custom task runners or scripts"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Automation tasks configurations (package.json scripts or Makefile) exist" if has_automated_tasks else "Missing structured automation runners"
    })
    
    signals.append({
        "signal": "lockfile_hygiene",
        "label": "Ecosystem package hygiene controls",
        "status": "PRESENT" if has_lockfile else "ABSENT",
        "evidence": ["Dependency lockfile present" if has_lockfile else "No lockfiles found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Ecosystem lockfile tracks exact dependency hashes" if has_lockfile else "Missing lockfile; dependencies may float unchecked"
    })
    
    signals.append({
        "signal": "ci_config",
        "label": "Continuous integration configurations",
        "status": "PRESENT" if any(p.startswith(".github/workflows/") for p in tree_paths) else "ABSENT",
        "evidence": ["GitHub Actions workflows present" if any(p.startswith(".github/workflows/") for p in tree_paths) else "No workflow files detected"],
        "applicability": "APPLICABLE",
        "weight": 10,
        "reason": "CI integration workflows configured to test and validate changes" if any(p.startswith(".github/workflows/") for p in tree_paths) else "Missing CI configuration definitions"
    })

    applicable_signals = []
    not_applicable_signals = []
    strengths = []
    weaknesses = []
    
    total_applicable_weight = 0
    earned_applicable_weight = 0
    
    for s in signals:
        rulesApplied.append(f"{s['signal']} = {'applicable' if s['applicability'] == 'APPLICABLE' else 'na'} (status: {s['status']})")
        if s["applicability"] == "APPLICABLE":
            total_applicable_weight += s["weight"]
            applicable_signals.append(s["label"])
            if s["status"] == "PRESENT":
                earned_applicable_weight += s["weight"]
                strengths.append(s["label"])
                evidence.append(f"✓ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"cq-{s['signal']}", "positive", "Code Quality", s["label"], s["evidence"][0]))
            else:
                weaknesses.append(s["label"])
                evidence.append(f"✗ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"cq-{s['signal']}", "warning", "Code Quality", f"Missing {s['label'].lower()}", f"{s['evidence'][0]} — applicable to this repository."))
        else:
            not_applicable_signals.append(s["label"])
            evidence.append(f"⊖ {s['label']} (N/A)")
            findings.append(create_finding(
                f"cq-{s['signal']}", 
                "info", 
                "Code Quality", 
                f"{s['label']} not applicable", 
                f"This code quality signal is not required for {repo_type} repositories."
            ))

    score = round((earned_applicable_weight / total_applicable_weight) * 100) if total_applicable_weight > 0 else 100

    rawMetrics.update({
        "hasLint": has_lint_config, "hasFormat": has_format_config, "hasTs": has_typing_config, "hasStructure": True,
        "testRatio": test_ratio, "scriptScore": 10 if has_automated_tasks else 0, "languageCount": len(languages), "sourceFileCount": len(source_files), "testFileCount": len(test_files)
    })
    
    if score >= 90: summary = "Exceptional code quality and tooling practices detected."
    elif score >= 80: summary = "Strong code quality setup with minor tooling gaps."
    elif score >= 70: summary = "Good code quality structure matching expected standards."
    elif score >= 60: summary = "Fair quality setup containing minor gaps."
    elif score >= 40: summary = "Basic quality controls that need enhancement."
    else: summary = "Code quality tooling needs significant attention."
    
    if score >= 80:
        recommendation = "Maintain current standards and continue code formatting consistency checks."
    else:
        recommendation = "Incorporate linters, formatters, and static checks to enforce code consistency."

    max_score = 100
    confidence = calculate_confidence(len(evidence), True, len(limitations))
    confidenceReason = "Code quality analysis evaluated based on tooling markers"

    return create_dimension("codeQuality", "Code Quality", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason, strengths, weaknesses, applicable_signals, not_applicable_signals, signals)


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
    
    classification = input_data.get("classification", {})
    repo_type = classification.get("type", "UNKNOWN")
    
    tree = input_data.get("tree", [])
    tree_paths = [t.get("path", "") for t in tree]
    readme = input_data.get("readme", "")
    
    has_readme = bool(readme)
    if not has_readme:
        findings.append(create_finding("doc-no-readme", "critical", "Documentation", "No README found", "Repository lacks a README.md file.", [], None, "Create a README.md at the project root."))
        
    has_description = False
    if readme:
        lines = [l for l in readme.split('\n') if l.strip()]
        has_description = any(not l.startswith("#") and len(l.strip()) > 20 for l in lines)
        
    has_install = False
    if readme:
        install_regex = re.compile(r'install|setup|getting.started|quick.start|dependency|requirements', re.IGNORECASE)
        has_install = bool(install_regex.search(readme)) or get_section_depth(readme, install_regex) > 3
        
    has_usage = False
    if readme:
        usage_regex = re.compile(r'usage|how.to.use|quick.start|commands|running|run', re.IGNORECASE)
        has_usage = bool(usage_regex.search(readme)) or get_section_depth(readme, usage_regex) > 3
        
    has_examples = False
    if readme:
        example_regex = re.compile(r'example|demo|sample|snippet|preview', re.IGNORECASE)
        has_examples = bool(example_regex.search(readme)) or get_section_depth(readme, example_regex) > 2
        
    has_config_docs = False
    if readme:
        has_config_docs = bool(re.search(r'config|environment|env|\.env|variable|option', readme, re.IGNORECASE))
    
    has_arch_docs = False
    if readme:
        has_arch_docs = bool(re.search(r'architecture|design|overview|api|endpoint|interface|folder.structure|directory.structure', readme, re.IGNORECASE))
    has_docs_dir = any(t.get("path", "").startswith("docs/") for t in tree)
    
    has_license = bool(input_data.get("license")) or any(t.get("path") in ["LICENSE", "LICENSE.txt", "license", "LICENSE.md"] for t in tree)
    if not has_license:
        findings.append(create_finding("doc-no-license", "warning", "Documentation", "No LICENSE file found", "Repository lacks a license file to clarify usage rights.", [], None, "Add a LICENSE file at the project root."))
        
    has_contributing = bool(input_data.get("contributing")) or any(t.get("path") in ["CONTRIBUTING.md", "contributing.md"] for t in tree)
    has_security = bool(input_data.get("security")) or any(t.get("path") in ["SECURITY.md", "security.md"] for t in tree)
    has_changelog = bool(input_data.get("changelog")) or any(t.get("path") in ["CHANGELOG", "CHANGELOG.md"] for t in tree)
    has_codeowners = bool(input_data.get("codeowners")) or any(t.get("path") in ["CODEOWNERS", ".github/CODEOWNERS"] for t in tree)
    has_templates = any(t.get("path", "").startswith(".github/ISSUE_TEMPLATE") or t.get("path", "").startswith(".github/PULL_REQUEST_TEMPLATE") for t in tree)
    
    has_screenshots = False
    if readme:
        has_screenshots = bool(re.search(r'screenshot|image|gif|demo|video|preview', readme, re.IGNORECASE) and re.search(r'!\[.*\]\(.*\)', readme, re.IGNORECASE))

    is_curated = repo_type in ["CURATED_LIST", "DOCUMENTATION", "DATASET"]

    signals = []
    
    signals.append({
        "signal": "readme_exists",
        "label": "README file exists",
        "status": "PRESENT" if has_readme else "ABSENT",
        "evidence": ["README.md found in repository root" if has_readme else "No README.md file detected"],
        "applicability": "APPLICABLE",
        "weight": 20,
        "reason": "Project documentation entry point file exists" if has_readme else "Missing README files"
    })
    
    signals.append({
        "signal": "description",
        "label": "Project purpose definition",
        "status": "PRESENT" if has_description else "ABSENT",
        "evidence": ["Descriptive purpose statements found in README" if has_description else "No project description paragraphs found"],
        "applicability": "APPLICABLE",
        "weight": 15,
        "reason": "Clear project scope and purpose declaration paragraph in README" if has_description else "Missing quick description of what this project does"
    })
    
    signals.append({
        "signal": "installation",
        "label": "Installation or setup guidelines",
        "status": "PRESENT" if has_install else "ABSENT",
        "evidence": ["Detailed setup or build instructions detected" if has_install else "No setup instructions found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Setup steps, command triggers or build templates documented" if has_install else "No setup guides found in README"
    })
    
    signals.append({
        "signal": "usage",
        "label": "Usage instruction guidelines",
        "status": "PRESENT" if has_usage else "ABSENT",
        "evidence": ["Usage commands or guidelines detected in README" if has_usage else "No usage guidelines found"],
        "applicability": "APPLICABLE",
        "weight": 15,
        "reason": "Command parameters or basic operation instructions configured" if has_usage else "No usage guide sections found in README"
    })
    
    signals.append({
        "signal": "examples",
        "label": "Practical code examples or visuals",
        "status": "PRESENT" if (has_examples or has_screenshots) else "ABSENT",
        "evidence": ["Code snippets, screenshots, or demo targets present" if (has_examples or has_screenshots) else "No demos or visual assets found"],
        "applicability": "APPLICABLE",
        "weight": 15,
        "reason": "Code block blocks or embedded visual screenshots present" if (has_examples or has_screenshots) else "Missing practical code samples or images"
    })
    
    signals.append({
        "signal": "contributing",
        "label": "Contribution guide guidelines",
        "status": "PRESENT" if has_contributing else "ABSENT",
        "evidence": ["CONTRIBUTING file or section found in tree" if has_contributing else "No contribution guidelines found"],
        "applicability": "APPLICABLE",
        "weight": 10,
        "reason": "Community contribution protocols file or section present" if has_contributing else "No contributor guidelines found"
    })
    
    signals.append({
        "signal": "license",
        "label": "Clarified LICENSE file",
        "status": "PRESENT" if has_license else "ABSENT",
        "evidence": ["LICENSE file present at root" if has_license else "No license guidelines detected"],
        "applicability": "APPLICABLE",
        "weight": 10,
        "reason": "Open source usage permissions explicitly declared" if has_license else "No license file; permissions are undefined"
    })
    
    signals.append({
        "signal": "architecture_docs",
        "label": "Architecture design overview",
        "status": "PRESENT" if (has_arch_docs or has_docs_dir) else "ABSENT",
        "evidence": ["Architecture designs, folder structures, or API routes documented" if (has_arch_docs or has_docs_dir) else "No architecture details found"],
        "applicability": "APPLICABLE",
        "weight": 5,
        "reason": "Directory structure overview or conceptual flow diagrams present" if (has_arch_docs or has_docs_dir) else "Missing structured architecture layouts documentation"
    })

    applicable_signals = []
    not_applicable_signals = []
    strengths = []
    weaknesses = []
    
    total_applicable_weight = 0
    earned_applicable_weight = 0
    
    for s in signals:
        rulesApplied.append(f"{s['signal']} = {'applicable' if s['applicability'] == 'APPLICABLE' else 'na'} (status: {s['status']})")
        if s["applicability"] == "APPLICABLE":
            total_applicable_weight += s["weight"]
            applicable_signals.append(s["label"])
            if s["status"] == "PRESENT":
                earned_applicable_weight += s["weight"]
                strengths.append(s["label"])
                evidence.append(f"✓ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"doc-{s['signal']}", "positive", "Documentation", s["label"], s["evidence"][0]))
            else:
                weaknesses.append(s["label"])
                evidence.append(f"✗ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"doc-{s['signal']}", "warning", "Documentation", f"Missing {s['label'].lower()}", f"{s['evidence'][0]} — applicable to this repository."))
        else:
            not_applicable_signals.append(s["label"])
            evidence.append(f"⊖ {s['label']} (N/A)")
            findings.append(create_finding(
                f"doc-{s['signal']}", 
                "info", 
                "Documentation", 
                f"{s['label']} not applicable", 
                f"This documentation signal is not required for {repo_type} repositories."
            ))

    score = round((earned_applicable_weight / total_applicable_weight) * 100) if total_applicable_weight > 0 else 100
    
    rawMetrics.update({
        "hasReadme": has_readme, "hasDescription": has_description, "hasInstall": has_install, "hasUsage": has_usage,
        "hasExamples": has_examples, "hasConfigDocs": has_config_docs, "hasArchDocs": has_arch_docs or has_docs_dir,
        "hasLicense": has_license, "hasContributing": has_contributing, "hasSecurityDoc": has_security,
        "hasChangelog": has_changelog, "hasCodeowners": has_codeowners, "hasTemplates": has_templates, "hasScreenshots": has_screenshots,
        "readmeLength": len(readme) if readme else 0
    })
    
    if not readme: limitations.append("README content not available for analysis")
    
    if score >= 90: summary = "Exceptional documentation layout covering all essential signals."
    elif score >= 80: summary = "Strong documentation coverage with clear usage guides."
    elif score >= 70: summary = "Good documentation matching expected guidelines."
    elif score >= 60: summary = "Fair documentation containing minor instruction gaps."
    elif score >= 40: summary = "Basic documentation that needs substantial enhancement."
    else: summary = "Documentation needs significant work."
    
    if score >= 80: recommendation = "Keep documentation updated with codebase structure updates."
    else: recommendation = "Improve README with installation, usage instructions, examples, and licensing indicators."

    max_score = 100
    confidence = calculate_confidence(len(evidence), bool(readme), len(limitations))
    confidenceReason = "README not available — limited documentation analysis" if not readme else ("Comprehensive documentation evidence available" if len(evidence) >= 10 else "Partial documentation evidence available")

    return create_dimension("documentation", "Documentation", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason, strengths, weaknesses, applicable_signals, not_applicable_signals, signals)


def analyze_security(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = ["Deep vulnerability scanning (SAST/DAST) not included — analysis limited to file-level signals"]
    rawMetrics = {}
    
    classification = input_data.get("classification", {})
    repo_type = classification.get("type", "UNKNOWN")
    
    tree = input_data.get("tree", [])
    tree_paths = [t.get("path", "") for t in tree]
    
    has_security_md = bool(input_data.get("security")) or any(t.get("path") in ["SECURITY.md", "security.md"] for t in tree)
    
    env_files = [t for t in tree if t.get("path") in [".env", ".env.local", ".env.production", ".env.development"] or re.match(r'^\.env\.', t.get("path", ""))]
    has_tracked_env = len(env_files) > 0
    
    has_gitignore = any(t.get("path") == ".gitignore" for t in tree)
    
    has_dependabot = any(t.get("path") in [".github/dependabot.yml", ".github/dependabot.yaml"] for t in tree)
    
    security_workflows = [t for t in tree if t.get("path", "").startswith(".github/workflows/") and any(x in t.get("path", "").lower() for x in ["security", "codeql", "snyk", "trivy"])]
    has_security_ci = len(security_workflows) > 0
    
    key_patterns = [re.compile(r'\.pem$'), re.compile(r'\.key$'), re.compile(r'\.p12$'), re.compile(r'\.pfx$'), re.compile(r'\.jks$'), re.compile(r'id_rsa'), re.compile(r'id_ed25519'), re.compile(r'id_dsa'), re.compile(r'id_ecdsa'), re.compile(r'\.keystore$')]
    key_files = [t for t in tree if any(p.search(t.get("path", "")) for p in key_patterns)]
    has_keys = len(key_files) > 0
    
    lock_files = ["package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "Pipfile.lock", "Cargo.lock", "go.sum", "requirements.txt"]
    has_lock = any(any(t.get("path") == l for t in tree) for l in lock_files)
    
    has_dockerfile = any(t.get("path") == "Dockerfile" for t in tree)
    has_dockerignore = any(t.get("path") == ".dockerignore" for t in tree)

    is_curated = repo_type in ["CURATED_LIST", "DOCUMENTATION", "DATASET", "EDUCATIONAL"]

    signals = []
    
    signals.append({
        "signal": "gitignore",
        "label": "Tracked files ignore filters",
        "status": "PRESENT" if has_gitignore else "ABSENT",
        "evidence": [".gitignore configuration found" if has_gitignore else "No ignore controls defined"],
        "applicability": "APPLICABLE",
        "weight": 15,
        "reason": "Exclusion rules prevent tracking temporary build or environment variables files" if has_gitignore else "Missing files ignore filters configuration"
    })
    
    signals.append({
        "signal": "lockfile",
        "label": "Ecosystem dependency lockfile",
        "status": "PRESENT" if has_lock else "ABSENT",
        "evidence": ["Ecosystem lockfile found" if has_lock else "No lockfile present"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Tracking package-lock.json or equivalent locks dependency versions" if has_lock else "Missing package versions lock files"
    })
    
    signals.append({
        "signal": "security_md",
        "label": "Project security guidelines",
        "status": "PRESENT" if has_security_md else "ABSENT",
        "evidence": ["SECURITY.md guidelines present" if has_security_md else "No SECURITY.md file found"],
        "applicability": "APPLICABLE",
        "weight": 10,
        "reason": "Responsible disclosure policy guidelines present" if has_security_md else "Responsible disclosure guidelines not defined"
    })
    
    signals.append({
        "signal": "dependabot",
        "label": "Automated security updates",
        "status": "PRESENT" if has_dependabot else "ABSENT",
        "evidence": ["Dependabot configuration present" if has_dependabot else "No dependabot config found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Automated dependency updates configured" if has_dependabot else "Missing automated vulnerability updater configs"
    })
    
    signals.append({
        "signal": "security_ci",
        "label": "Continuous security testing",
        "status": "PRESENT" if has_security_ci else "ABSENT",
        "evidence": ["SAST scan action configured in workflows" if has_security_ci else "No security scanners in workflows"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Static analysis vulnerability scan triggers integrated" if has_security_ci else "No continuous vulnerability scanner workflows configured"
    })
    
    signals.append({
        "signal": "no_tracked_env",
        "label": "No exposed environment parameters",
        "status": "PRESENT" if not has_tracked_env else "ABSENT",
        "evidence": ["No credentials files tracked" if not has_tracked_env else f"Tracked secret files found: {', '.join(f.get('path') for f in env_files)}"],
        "applicability": "APPLICABLE",
        "weight": 20,
        "reason": "Local credentials configuration parameters are not committed to source history" if not has_tracked_env else "Sensitive local env properties committed in repo tree"
    })
    
    signals.append({
        "signal": "no_keys",
        "label": "No private keys exposure",
        "status": "PRESENT" if not has_keys else "ABSENT",
        "evidence": ["No key files detected in tree" if not has_keys else f"Tracked private keys found: {', '.join(f.get('path') for f in key_files)}"],
        "applicability": "APPLICABLE",
        "weight": 20,
        "reason": "No exposed public key infrastructure templates found" if not has_keys else "Sensitive private keys committed to source history"
    })

    applicable_signals = []
    not_applicable_signals = []
    strengths = []
    weaknesses = []
    
    total_applicable_weight = 0
    earned_applicable_weight = 0
    
    for s in signals:
        rulesApplied.append(f"{s['signal']} = {'applicable' if s['applicability'] == 'APPLICABLE' else 'na'} (status: {s['status']})")
        if s["applicability"] == "APPLICABLE":
            total_applicable_weight += s["weight"]
            applicable_signals.append(s["label"])
            if s["status"] == "PRESENT":
                earned_applicable_weight += s["weight"]
                strengths.append(s["label"])
                evidence.append(f"✓ {s['label']}: {s['evidence'][0]}")
                if s["signal"] not in ["no_tracked_env", "no_keys"]:
                    findings.append(create_finding(f"sec-{s['signal']}", "positive", "Security", s["label"], s["evidence"][0]))
            else:
                weaknesses.append(s["label"])
                evidence.append(f"✗ {s['label']}: {s['evidence'][0]}")
                
                # Separate process gaps from actual exposures
                if s["signal"] == "no_tracked_env":
                    findings.append(create_finding("sec-env", "critical", "Security", "Environment credentials tracked", f"Exposed tracked env parameters: {', '.join(f.get('path') for f in env_files)}", [f.get("path") for f in env_files], None, "Remove tracked env files immediately, add to .gitignore and rotate exposed keys."))
                elif s["signal"] == "no_keys":
                    findings.append(create_finding("sec-keys", "critical", "Security", "Tracked private keys exposed", f"Tracked private keys found in tree: {', '.join(f.get('path') for f in key_files)}", [f.get("path") for f in key_files], None, "Revoke all exposed keys immediately and delete from repository index."))
                elif s["signal"] == "security_md":
                    findings.append(create_finding("sec-security_md", "info", "Security", "Missing security guidelines", "No SECURITY.md file found. Documenting security reporting guidelines is a good software engineering practice.", [], None, "Add a SECURITY.md file to outline how users can report vulnerabilities safely."))
                elif s["signal"] == "dependabot":
                    findings.append(create_finding("sec-dependabot", "low", "Security", "Missing automated security updates", "No Dependabot configuration found. Automated updates monitor dependencies for security alerts.", [], None, "Add a .github/dependabot.yml config file."))
                elif s["signal"] == "security_ci":
                    findings.append(create_finding("sec-security_ci", "low", "Security", "Missing continuous security testing", "Continuous application security testing (SAST) is not configured in workflows.", [], None, "Integrate CodeQL or Snyk vulnerability scanners into the CI workflows."))
                else:
                    findings.append(create_finding(f"sec-{s['signal']}", "warning", "Security", f"Missing {s['label'].lower()}", f"{s['evidence'][0]} — this is applicable to this project type."))
        else:
            not_applicable_signals.append(s["label"])
            evidence.append(f"⊖ {s['label']} (N/A)")
            findings.append(create_finding(
                f"sec-{s['signal']}", 
                "info", 
                "Security", 
                f"{s['label']} not applicable", 
                f"This security control is not required for {repo_type} repositories."
            ))

    score = round((earned_applicable_weight / total_applicable_weight) * 100) if total_applicable_weight > 0 else 100

    if has_dockerfile and not has_dockerignore:
        findings.append(create_finding("sec-docker", "warning", "Security", "Docker without .dockerignore configuration", "Dockerfile found but no .dockerignore, risking sensitive files inclusion in image build targets.", [], "Dockerfile", "Add a .dockerignore file at the project root."))

    rawMetrics.update({
        "hasSecurityMd": has_security_md, "hasTrackedEnv": has_tracked_env, "envFileCount": len(env_files),
        "hasGitignore": has_gitignore, "hasDependabot": has_dependabot, "securityWorkflowCount": len(security_workflows),
        "keyFileCount": len(key_files), "hasLock": has_lock, "hasDockerfile": has_dockerfile
    })
    
    if score >= 90: summary = "Exceptional security posture with clean credentials isolation."
    elif score >= 80: summary = "Strong security setup with minor policy/maintenance gaps."
    elif score >= 70: summary = "Good security hygiene matching standard practices."
    elif score >= 60: summary = "Fair security setup containing minor gaps."
    elif score >= 40: summary = "Some security measures but significant credential risks exist."
    else: summary = "Security posture needs immediate attention."
    
    if score >= 80: recommendation = "Maintain current standards and run periodic automated credential sweep audits."
    else: recommendation = "Address exposed parameters, add .gitignore settings, and configure security guidelines."

    max_score = 100
    confidence = calculate_confidence(len(evidence), True, len(limitations))
    confidenceReason = "Critical security issues detected with high confidence" if (has_tracked_env or has_keys) else "Security analysis based on file configurations"

    return create_dimension("security", "Security", score, max_score, 15, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason, strengths, weaknesses, applicable_signals, not_applicable_signals, signals)


def analyze_testing(input_data: dict) -> dict:
    findings = []
    evidence = []
    rulesApplied = []
    limitations = []
    rawMetrics = {}
    
    classification = input_data.get("classification", {})
    repo_type = classification.get("type", "UNKNOWN")
    
    tree = input_data.get("tree", [])
    tree_paths = [t.get("path", "") for t in tree]
    
    test_file_patterns = [
        re.compile(r'\.(test|spec)\.(tsx?|jsx?|ts|js)$'), re.compile(r'\.(test|spec)\.(py|go|rs|java|rb)$'),
        re.compile(r'__tests__'), re.compile(r'^tests?/'), re.compile(r'^spec/'), re.compile(r'\btest_', re.IGNORECASE), re.compile(r'_test\.', re.IGNORECASE)
    ]
    test_files = [t for t in tree if any(p.search(t.get("path", "")) for p in test_file_patterns)]
    test_file_count = len(set(f.get("path") for f in test_files))
    has_test_files = test_file_count > 0
    
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
        detected_framework = "pytest"
    if not detected_framework and any(t.get("path") in ["pom.xml", "build.gradle", "build.gradle.kts"] for t in tree):
        detected_framework = "JUnit"
    if not detected_framework and any(t.get("path") == "go.mod" for t in tree) and test_file_count > 0:
        detected_framework = "Go testing"
    if not detected_framework and any(t.get("path") == "Cargo.toml" for t in tree) and test_file_count > 0:
        detected_framework = "Rust testing"
        
    has_framework = bool(detected_framework)
    
    has_test_script = False
    test_script_name = ""
    pkg = input_data.get("packageJson", {})
    if pkg and isinstance(pkg.get("scripts"), dict):
        test_keys = [k for k in pkg.get("scripts", {}).keys() if k == "test" or "test" in k or "spec" in k]
        if test_keys:
            has_test_script = True
            test_script_name = test_keys[0]
            
    ci_test_workflows = [t for t in tree if t.get("path", "").startswith(".github/workflows/") and any(x in t.get("path", "") for x in ["test", "ci", "check"])]
    has_ci_tests = len(ci_test_workflows) > 0
    
    has_coverage = False
    if pkg and isinstance(pkg.get("scripts"), dict):
        has_coverage = any("coverage" in k or ("coverage" in (pkg["scripts"][k] or "")) for k in pkg.get("scripts", {}).keys())
    if not has_coverage:
        coverage_indicators = ["jest.config.js", "jest.config.ts", ".nycrc", ".nycrc.json", ".nycrc.yml", "vitest.config.ts", "vitest.config.js", "coverage/"]
        has_coverage = any(any(t.get("path") == c or t.get("path", "").startswith(c) for t in tree) for c in coverage_indicators)
        
    test_helpers = [t for t in tree if any(x in t.get("path", "") for x in ["test-utils", "testUtils", "setupTests", "setup.tests", "test-setup", "testSetup", "test.helper", "testHelper"])]
    has_test_helpers = len(test_helpers) > 0
    
    e2e_frameworks = ["playwright", "cypress", "puppeteer", "selenium"]
    has_e2e = any(
        any(fw in t.get("path", "") for t in tree) or
        (fw in (pkg.get("dependencies", {}) if isinstance(pkg.get("dependencies"), dict) else {})) or
        (fw in (pkg.get("devDependencies", {}) if isinstance(pkg.get("devDependencies"), dict) else {}))
        for fw in e2e_frameworks
    )

    is_curated = repo_type in ["CURATED_LIST", "DOCUMENTATION", "DATASET", "EDUCATIONAL"]

    signals = []
    
    signals.append({
        "signal": "test_files",
        "label": "Test suite modules",
        "status": "PRESENT" if has_test_files else "ABSENT",
        "evidence": [f"{test_file_count} test files detected in tree" if has_test_files else "No test suite modules found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 25,
        "reason": "Test suite code files are present in the repository" if has_test_files else "No unit or integration test files detected in project tree"
    })
    
    signals.append({
        "signal": "test_framework",
        "label": "Test runner framework configuration",
        "status": "PRESENT" if has_framework else "ABSENT",
        "evidence": [f"Test config for {detected_framework} found" if has_framework else "No test framework configuration detected"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 20,
        "reason": "Test framework settings or runner settings found" if has_framework else "Missing runner config files"
    })
    
    signals.append({
        "signal": "test_script",
        "label": "Test invocation commands",
        "status": "PRESENT" if has_test_script else "ABSENT",
        "evidence": [f"Test script '{test_script_name}' found" if has_test_script else "No test runner script in package.json"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Execution script commands configured for testing" if has_test_script else "No CLI test command target mapped in scripts"
    })
    
    signals.append({
        "signal": "ci_tests",
        "label": "Continuous testing integrations",
        "status": "PRESENT" if has_ci_tests else "ABSENT",
        "evidence": ["Continuous integration workflows running tests detected" if has_ci_tests else "No CI workflow testing actions found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 15,
        "reason": "Automated workflow steps execute test checks" if has_ci_tests else "CI pipeline does not run automated tests"
    })
    
    signals.append({
        "signal": "coverage",
        "label": "Test statement coverage reporting",
        "status": "PRESENT" if has_coverage else "ABSENT",
        "evidence": ["Test coverage reporting config found" if has_coverage else "No test coverage configurations found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Coverage tracking statistics setups discovered" if has_coverage else "Test code coverage reports not configured"
    })
    
    signals.append({
        "signal": "test_helpers",
        "label": "Mock or mock-setup helpers",
        "status": "PRESENT" if has_test_helpers else "ABSENT",
        "evidence": ["Setup files or testing helper utils present" if has_test_helpers else "No test setup helpers found"],
        "applicability": "APPLICABLE" if not is_curated else "NOT_APPLICABLE",
        "weight": 5,
        "reason": "Mock or runner configuration setup files detected" if has_test_helpers else "No test-specific initialization files found"
    })
    
    signals.append({
        "signal": "e2e",
        "label": "End-to-end testing integrations",
        "status": "PRESENT" if has_e2e else "ABSENT",
        "evidence": ["E2E testing configuration/library detected" if has_e2e else "No E2E testing configurations found"],
        "applicability": "APPLICABLE" if not is_curated and repo_type == "APPLICATION" else "NOT_APPLICABLE",
        "weight": 10,
        "reason": "Integration or browser mock testing libraries found" if has_e2e else "No end-to-end user path testing configurations setup"
    })

    applicable_signals = []
    not_applicable_signals = []
    strengths = []
    weaknesses = []
    
    total_applicable_weight = 0
    earned_applicable_weight = 0
    
    for s in signals:
        rulesApplied.append(f"{s['signal']} = {'applicable' if s['applicability'] == 'APPLICABLE' else 'na'} (status: {s['status']})")
        if s["applicability"] == "APPLICABLE":
            total_applicable_weight += s["weight"]
            applicable_signals.append(s["label"])
            if s["status"] == "PRESENT":
                earned_applicable_weight += s["weight"]
                strengths.append(s["label"])
                evidence.append(f"✓ {s['label']}: {s['evidence'][0]}")
                findings.append(create_finding(f"test-{s['signal']}", "positive", "Testing", s["label"], s["evidence"][0]))
            else:
                weaknesses.append(s["label"])
                evidence.append(f"✗ {s['label']}: {s['evidence'][0]}")
                if s["signal"] == "test_files" and not has_framework:
                    findings.append(create_finding("test-none", "warning", "Testing", "No testing infrastructure detected", "No test files or configurations found in repository tree.", [], None, "Set up a test runner (e.g. pytest or Jest) and write tests."))
                else:
                    findings.append(create_finding(f"test-{s['signal']}", "warning", "Testing", f"Missing {s['label'].lower()}", f"{s['evidence'][0]} — applicable to this repository structure."))
        else:
            not_applicable_signals.append(s["label"])
            evidence.append(f"⊖ {s['label']} (N/A)")
            findings.append(create_finding(
                f"test-{s['signal']}", 
                "info", 
                "Testing", 
                f"{s['label']} not applicable", 
                f"Testing signals are not penalized because this repository classification type is {repo_type}."
            ))

    score = round((earned_applicable_weight / total_applicable_weight) * 100) if total_applicable_weight > 0 else 100

    rawMetrics.update({
        "testFileCount": test_file_count, "detectedFramework": detected_framework or "none", "hasTestScript": has_test_script,
        "hasCITests": has_ci_tests, "hasCoverage": has_coverage, "hasTestHelpers": has_test_helpers, "hasE2E": has_e2e
    })
    
    if test_file_count == 0: limitations.append("No test files found — analysis limited to configuration detection")
    
    if score >= 90: summary = "Exceptional testing setup with robust integration checks."
    elif score >= 80: summary = "Strong testing coverage with structured runner config."
    elif score >= 70: summary = "Good testing structure matching recommended standards."
    elif score >= 60: summary = "Fair testing setup containing minor coverage gaps."
    elif score >= 40: summary = "Basic testing integration with substantial coverage gaps."
    else: summary = "No testing infrastructure found."
    
    if score >= 80: recommendation = "Maintain current testing suites and continue automated execution check setups."
    else: recommendation = "Integrate a unit test runner framework and verify build targets in workflow scripts."

    max_score = 100
    confidence = calculate_confidence(len(evidence), test_file_count > 0 or has_framework, len(limitations))
    confidenceReason = "Test files found in repository — high confidence" if test_file_count > 0 else ("Test framework config found but no test files visible" if has_framework else "No testing evidence found")

    return create_dimension("testing", "Testing", score, max_score, 10, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason, strengths, weaknesses, applicable_signals, not_applicable_signals, signals)
