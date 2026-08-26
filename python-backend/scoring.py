import re
from analyzers import analyze_architecture, analyze_code_quality, analyze_documentation, analyze_security

def base_dimensions(overrides=None):
    defaults = [
        {"id": "documentation", "name": "Documentation", "weight": 25, "applicable": True},
        {"id": "codeQuality", "name": "Code Quality", "weight": 25, "applicable": True},
        {"id": "architecture", "name": "Architecture", "weight": 25, "applicable": True},
        {"id": "security", "name": "Security", "weight": 25, "applicable": True},
    ]
    if not overrides:
        return defaults

    result = []
    for d in defaults:
        override = overrides.get(d["id"])
        if override:
            new_d = d.copy()
            new_d.update(override)
            result.append(new_d)
        else:
            result.append(d.copy())
    return result

PROFILES = {
    "APPLICATION": {
        "type": "APPLICATION",
        "label": "Application",
        "description": "Software application with runtime code, deployment, and architecture",
        "dimensions": base_dimensions()
    },
    "LIBRARY": {
        "type": "LIBRARY",
        "label": "Library",
        "description": "Reusable package with API surface, publishing metadata, and tests",
        "dimensions": base_dimensions({
            "architecture": {"weight": 20}
        })
    },
    "CURATED_LIST": {
        "type": "CURATED_LIST",
        "label": "Curated List",
        "description": "Awesome-list, resource directory, or curated collection",
        "dimensions": base_dimensions({
            "codeQuality": {
                "weight": 0,
                "applicable": False,
                "notApplicableReason": "Curated lists contain minimal executable code"
            },
            "architecture": {
                "weight": 0,
                "applicable": False,
                "notApplicableReason": "No application architecture in a curated list"
            }
        })
    },
    "DATASET": {
        "type": "DATASET",
        "label": "Dataset",
        "description": "Data repository with schema, data files, and documentation",
        "dimensions": base_dimensions({
            "codeQuality": {"weight": 10},
            "architecture": {"weight": 10}
        })
    },
    "DOCUMENTATION": {
        "type": "DOCUMENTATION",
        "label": "Documentation",
        "description": "Documentation-focused repository with wiki-like content",
        "dimensions": base_dimensions({
            "codeQuality": {"weight": 10},
            "architecture": {"weight": 10}
        })
    },
    "EDUCATIONAL": {
        "type": "EDUCATIONAL",
        "label": "Educational",
        "description": "Tutorial, course, or educational content",
        "dimensions": base_dimensions({
            "architecture": {"weight": 15}
        })
    },
    "FRAMEWORK": {
        "type": "FRAMEWORK",
        "label": "Framework",
        "description": "Framework or SDK with multiple packages",
        "dimensions": base_dimensions()
    },
    "CLI_TOOL": {
        "type": "CLI_TOOL",
        "label": "CLI Tool",
        "description": "Command-line interface tool",
        "dimensions": base_dimensions({
            "architecture": {"weight": 15}
        })
    },
    "MONOREPO": {
        "type": "MONOREPO",
        "label": "Monorepo",
        "description": "Multi-package monorepo with multiple projects",
        "dimensions": base_dimensions()
    },
    "UNKNOWN": {
        "type": "UNKNOWN",
        "label": "General",
        "description": "Unclassified repository — using general scoring profile",
        "dimensions": base_dimensions()
    }
}
PROFILES["CONFIGURATION"] = PROFILES["UNKNOWN"]

def get_profile(repo_type):
    return PROFILES.get(repo_type, PROFILES["UNKNOWN"])

CURATED_LIST_KEYWORDS = [
    re.compile(r'awesome[.\s-]', re.I),
    re.compile(r'curated', re.I),
    re.compile(r'collection of', re.I),
    re.compile(r'list of', re.I),
    re.compile(r'resources? for', re.I),
    re.compile(r'directory of', re.I),
    re.compile(r'hub for', re.I),
    re.compile(r'compilation of', re.I),
    re.compile(r'handpicked', re.I),
    re.compile(r'best of', re.I),
]

DATASET_KEYWORDS = [
    re.compile(r'dataset', re.I),
    re.compile(r'data set', re.I),
    re.compile(r'training data', re.I),
    re.compile(r'benchmark', re.I),
    re.compile(r'corpus', re.I),
    re.compile(r'data for', re.I),
]

EDUCATIONAL_KEYWORDS = [
    re.compile(r'tutorial', re.I),
    re.compile(r'learn', re.I),
    re.compile(r'course', re.I),
    re.compile(r'workshop', re.I),
    re.compile(r'bootcamp', re.I),
    re.compile(r'exercise', re.I),
    re.compile(r'curriculum', re.I),
    re.compile(r'teaching', re.I),
    re.compile(r'education', re.I),
]

def classify_repository(input_data):
    repo = input_data.get('repo', {})
    tree = input_data.get('tree', [])
    languages = input_data.get('languages', {})
    readme = input_data.get('readme', "")
    if readme is None:
        readme = ""
        
    signals = []
    scores = {
        "APPLICATION": 0, "LIBRARY": 0, "CLI_TOOL": 0,
        "FRAMEWORK": 0, "DATASET": 0, "DOCUMENTATION": 0,
        "CURATED_LIST": 0, "EDUCATIONAL": 0, "CONFIGURATION": 0,
        "MONOREPO": 0, "UNKNOWN": 0,
    }

    description = (repo.get('description') or "").lower()
    readme_lower = readme.lower()
    tree_paths = [t.get('path', '') for t in tree]
    
    source_files = [t for t in tree if re.search(r'\.(ts|tsx|js|jsx|py|go|rs|java|rb|php|cs|cpp|c|swift|kt)$', t.get('path', ''))]
    markdown_files = [t for t in tree if t.get('path', '').endswith('.md')]
    data_files = [t for t in tree if re.search(r'\.(csv|json|yaml|yml|xml|parquet|tsv|sql)$', t.get('path', ''), re.I)]
    
    curated_keyword_count = 0
    for kw in CURATED_LIST_KEYWORDS:
        if kw.search(description):
            curated_keyword_count += 2
            signals.append("Curated list keyword in description")
        elif kw.search(readme_lower):
            curated_keyword_count += 1
            
    if curated_keyword_count >= 2:
        scores["CURATED_LIST"] += 25
        signals.append(f"{curated_keyword_count} curated list keyword matches")
    elif curated_keyword_count == 1:
        scores["CURATED_LIST"] += 10
        signals.append("Single curated list keyword in description")
        
    if len(markdown_files) > 5 and len(source_files) < len(markdown_files) * 0.3:
        scores["CURATED_LIST"] += 20
        signals.append("Markdown files dominate over source files")
        
    if readme and len(readme) > 10000:
        scores["CURATED_LIST"] += 10
        signals.append("Large README (>10KB) typical of curated lists")
        
    if len(source_files) > 10:
        scores["CURATED_LIST"] -= 20
        signals.append(f"{len(source_files)} source files reduce curated list likelihood")

    for kw in DATASET_KEYWORDS:
        if kw.search(description) or kw.search(readme_lower):
            scores["DATASET"] += 30
            signals.append("Dataset keyword detected")
            break
            
    if len(data_files) > len(source_files) and len(data_files) > 3:
        scores["DATASET"] += 20
        signals.append(f"{len(data_files)} data files exceed source files")
        
    for kw in EDUCATIONAL_KEYWORDS:
        if kw.search(description) or kw.search(readme_lower):
            scores["EDUCATIONAL"] += 25
            signals.append("Educational keyword detected")
            break
            
    app_dirs = ["src/", "app/", "pages/", "server/", "backend/", "frontend/", "api/", "routes/"]
    if any(any(p.startswith(d) for p in tree_paths) for d in app_dirs):
        scores["APPLICATION"] += 15
        scores["LIBRARY"] += 10
        signals.append("Application directory structure detected")
        
    deploy_files = ["Dockerfile", "docker-compose.yml", "vercel.json", "netlify.toml", "fly.toml"]
    if any(d in tree_paths for d in deploy_files):
        scores["APPLICATION"] += 15
        signals.append("Deployment configuration detected")
        
    entry_points = ["index.ts", "index.js", "main.ts", "main.js", "server.ts", "app.ts"]
    if any(e in tree_paths for e in entry_points):
        scores["APPLICATION"] += 10
        scores["LIBRARY"] += 10
        signals.append("Entry point detected")
        
    if "package.json" in tree_paths:
        scores["LIBRARY"] += 10
        scores["APPLICATION"] += 5
        signals.append("package.json detected")
    if "setup.py" in tree_paths or "pyproject.toml" in tree_paths:
        scores["LIBRARY"] += 15
        signals.append("Python package config detected")
    if "Cargo.toml" in tree_paths:
        scores["LIBRARY"] += 15
        signals.append("Rust crate detected")
    if "go.mod" in tree_paths:
        scores["LIBRARY"] += 15
        signals.append("Go module detected")
        
    framework_dirs = ["packages/", "lerna.json", "turbo.json", "nx.json"]
    if any(any(p.startswith(d) or p == d for p in tree_paths) for d in framework_dirs):
        scores["FRAMEWORK"] += 15
        scores["MONOREPO"] += 20
        signals.append("Monorepo/framework structure detected")
        
    cli_signals = ["bin/", "cli.ts", "cli.js", "cli.py", "cmd/"]
    if any(any(p.startswith(s) or p == s for p in tree_paths) for s in cli_signals):
        scores["CLI_TOOL"] += 20
        signals.append("CLI structure detected")
        
    config_files = [p for p in tree_paths if re.search(r'\.(config|rc|conf)\.(js|ts|json|yaml|yml)$', p) or re.search(r'^\.[a-z]+rc', p)]
    if len(config_files) > len(source_files) * 0.5 and len(source_files) < 5:
        scores["CONFIGURATION"] += 20
        signals.append("Configuration-heavy repository")
        
    docs_dirs = [p for p in tree_paths if p.startswith("docs/")]
    if len(docs_dirs) > 3 and len(source_files) < 5:
        scores["DOCUMENTATION"] += 20
        signals.append("Documentation-heavy repository")
        
    if len(markdown_files) > 10 and len(source_files) < 3:
        scores["DOCUMENTATION"] += 15
        signals.append("Many markdown files, few source files")
        
    has_meaningful_code = any(
        lang not in ["Markdown", "YAML", "JSON", "HTML", "CSS", "Dockerfile", "Shell"] and bytes_ > 1000 
        for lang, bytes_ in languages.items()
    )
    
    if not has_meaningful_code and len(languages) > 0:
        scores["CURATED_LIST"] += 10
        scores["DOCUMENTATION"] += 10
        signals.append("No meaningful executable code detected in languages")
        
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    winner, winner_score = sorted_scores[0]
    
    if winner_score < 20 and readme:
        list_items = len(re.findall(r'^[\s]*[-*]\s', readme, re.MULTILINE))
        headings = len(re.findall(r'^#{1,3}\s', readme, re.MULTILINE))
        if list_items > 20:
            scores["CURATED_LIST"] += 15
            signals.append(f"Many list items in README ({list_items})")
        if headings > 5 and list_items > headings * 3:
            scores["CURATED_LIST"] += 10
            signals.append("README structured as categorized list")
                
    final_sorted = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    final_winner, final_score = final_sorted[0]
    
    type_ = final_winner
    confidence = max(0.3, min(0.99, final_score / 60.0))
    
    reason_map = {
        "APPLICATION": "Detected application structure with deployment configuration",
        "LIBRARY": "Detected reusable package with publishing metadata",
        "CLI_TOOL": "Detected command-line interface structure",
        "FRAMEWORK": "Detected framework/monorepo structure",
        "DATASET": "Detected data-heavy repository with dataset characteristics",
        "DOCUMENTATION": "Detected documentation-focused repository",
        "CURATED_LIST": "Detected curated list / awesome-list / resource directory",
        "EDUCATIONAL": "Detected educational/tutorial content",
        "CONFIGURATION": "Detected configuration-focused repository",
        "MONOREPO": "Detected monorepo with multiple packages",
        "UNKNOWN": "Could not determine repository type from available signals",
    }
    
    return {
        "type": type_,
        "confidence": confidence,
        "reason": reason_map.get(type_, "Unknown reason"),
        "signals": signals
    }

def calculate_repository_score(input_data):
    dimension_scores = input_data.get('dimension_scores', [])
    classification = input_data.get('classification', {})
    
    profile = get_profile(classification.get('type'))
    
    contributions = []
    total_weight = 0
    weighted_sum = 0
    
    for profile_dim in profile['dimensions']:
        dim_score = next((d for d in dimension_scores if d.get('id') == profile_dim['id']), None)
        
        if not profile_dim.get('applicable', True):
            contributions.append({
                "dimension": profile_dim['id'],
                "dimensionName": profile_dim['name'],
                "score": 0,
                "maxScore": 100,
                "effectiveWeight": 0,
                "contribution": 0,
                "applicable": False,
                "notApplicableReason": profile_dim.get('notApplicableReason')
            })
            continue
            
        raw_score = 0
        if dim_score and dim_score.get('maxScore', 0) > 0:
            raw_score = (dim_score['score'] / dim_score['maxScore']) * 100
            
        effective_weight = profile_dim['weight']
        total_weight += effective_weight
        contribution = raw_score * (effective_weight / 100.0)
        weighted_sum += contribution
        
        contributions.append({
            "dimension": profile_dim['id'],
            "dimensionName": profile_dim['name'],
            "score": round(raw_score),
            "maxScore": 100,
            "effectiveWeight": effective_weight,
            "contribution": round(contribution * 10) / 10.0,
            "applicable": True
        })
        
    overall = round((weighted_sum / total_weight) * 100 * 10) / 10.0 if total_weight > 0 else 0
    rounded_overall = round(overall)
    
    normalized_contributions = []
    for c in contributions:
        if not c['applicable']:
            normalized_contributions.append(c)
            continue
        normalized_weight = (c['effectiveWeight'] / total_weight) * 100 if total_weight > 0 else 0
        normalized_contribution = c['score'] * (normalized_weight / 100.0)
        normalized_contributions.append({
            **c,
            "effectiveWeight": round(normalized_weight * 10) / 10.0,
            "contribution": round(normalized_contribution * 10) / 10.0
        })
        
    enriched_dimensions = []
    for d in dimension_scores:
        profile_dim = next((p for p in profile['dimensions'] if p['id'] == d.get('id')), None)
        if profile_dim and not profile_dim.get('applicable', True):
            new_d = d.copy()
            new_d.update({
                "score": 0,
                "findings": [],
                "status": "fair",
                "confidence": "high",
                "confidenceReason": profile_dim.get('notApplicableReason', "Not applicable to this repository type"),
                "summary": "N/A",
                "recommendation": "Not applicable to this repository type.",
                "limitations": d.get('limitations', []) + [f"Not applicable: {profile_dim.get('notApplicableReason')}"]
            })
            enriched_dimensions.append(new_d)
        else:
            enriched_dimensions.append(d)
            
    applicable_count = sum(1 for c in contributions if c['applicable'])
    not_applicable_count = sum(1 for c in contributions if not c['applicable'])
    
    conf_map = {"high": 0.95, "medium": 0.7, "low": 0.4}
    applicable_dims = [d for d in enriched_dimensions if next((p for p in profile['dimensions'] if p['id'] == d.get('id')), {}).get('applicable', True)]
    
    avg_confidence = 0.5
    if applicable_dims:
        avg_confidence = sum(conf_map.get(d.get('confidence', 'medium'), 0.7) for d in applicable_dims) / len(applicable_dims)
        
    return {
        "overall": rounded_overall,
        "profile": classification.get('type'),
        "profileLabel": profile['label'],
        "profileDescription": profile['description'],
        "classification": classification,
        "dimensions": enriched_dimensions,
        "weightedContributions": normalized_contributions,
        "applicableCount": applicable_count,
        "notApplicableCount": not_applicable_count,
        "confidence": round(avg_confidence * 100) / 100.0,
        "scoringVersion": "3.1"
    }

def get_resume_readiness_status(score):
    if score >= 80: return "exceptional"
    if score >= 60: return "ready"
    if score >= 40: return "needs_work"
    return "not_ready"

def calculate_resume_readiness(engineering_dimensions, raw_metrics, classification):
    profile = get_profile(classification.get('type'))
    
    def is_dim_applicable(dim_id):
        dim = next((d for d in profile['dimensions'] if d['id'] == dim_id), None)
        return dim.get('applicable', True) if dim else True
        
    is_code_applicable = is_dim_applicable("codeQuality")
    is_arch_applicable = is_dim_applicable("architecture")
    is_sec_applicable = is_dim_applicable("security")
    is_doc_applicable = is_dim_applicable("documentation")
    
    is_testing_applicable = is_code_applicable
    
    total_earned = 0
    total_max = 0
    
    strengths = []
    weaknesses = []
    before_resume = []
    applicable_signals = []
    excluded_dimensions = []
    evidence = []
    methodology = []
    
    if is_doc_applicable:
        doc_earned = 0
        doc_max = 25
        total_max += doc_max
        applicable_signals.append("Documentation")
        
        if raw_metrics.get('hasReadme'):
            doc_earned += 8
            strengths.append("README present")
        else:
            weaknesses.append("No README")
            before_resume.append("Add a comprehensive README")
            
        if raw_metrics.get('hasDescription'):
            doc_earned += 4
        else:
            weaknesses.append("No project description")
            before_resume.append("Add a clear project description to README")
            
        if raw_metrics.get('hasInstall'):
            doc_earned += 4
        else:
            weaknesses.append("No installation instructions")
            before_resume.append("Add setup/installation instructions")
            
        if raw_metrics.get('hasUsage'):
            doc_earned += 4
        else:
            weaknesses.append("No usage documentation")
            before_resume.append("Add usage instructions with examples")
            
        if raw_metrics.get('hasExamples'):
            doc_earned += 3
            strengths.append("Examples/demos present")
            
        if raw_metrics.get('hasScreenshots'):
            doc_earned += 2
            strengths.append("Visual documentation present")
            
        total_earned += doc_earned
        evidence.append(f"Documentation contribution: {doc_earned}/{doc_max}")
    else:
        excluded_dimensions.append("Documentation")
        
    if is_code_applicable:
        cq_earned = 0
        cq_max = 20
        total_max += cq_max
        applicable_signals.append("Code Quality")
        
        code_quality_dim = next((d for d in engineering_dimensions if d.get('id') == "codeQuality"), None)
        if code_quality_dim:
            cq_pct = (code_quality_dim['score'] / code_quality_dim['maxScore']) * 100 if code_quality_dim.get('maxScore', 0) > 0 else 0
            if cq_pct >= 70:
                strengths.append("Strong code quality tooling")
            elif cq_pct < 50:
                weaknesses.append("Code quality tooling needs improvement")
                before_resume.append("Add linting, formatting, and type checking")
            cq_earned = round(5 + (cq_pct / 100.0) * 15)
            
        total_earned += cq_earned
        evidence.append(f"Code Quality contribution: {cq_earned}/{cq_max}")
    else:
        excluded_dimensions.append("Code Quality")
        
    if is_testing_applicable:
        test_earned = 0
        test_max = 15
        total_max += test_max
        applicable_signals.append("Testing")
        
        if raw_metrics.get('hasTests'):
            test_earned = 15
            strengths.append("Test coverage present")
        elif raw_metrics.get('hasCI'):
            test_earned = 8
        else:
            weaknesses.append("No test evidence")
            before_resume.append("Add automated tests")
            
        total_earned += test_earned
        evidence.append(f"Testing contribution: {test_earned}/{test_max}")
    else:
        excluded_dimensions.append("Testing")
        
    if is_arch_applicable:
        arch_earned = 0
        arch_max = 15
        total_max += arch_max
        applicable_signals.append("Architecture")
        
        arch_dim = next((d for d in engineering_dimensions if d.get('id') == "architecture"), None)
        if arch_dim:
            arch_pct = (arch_dim['score'] / arch_dim['maxScore']) * 100 if arch_dim.get('maxScore', 0) > 0 else 0
            if arch_pct >= 70:
                strengths.append("Well-organized architecture")
            elif arch_pct < 50:
                weaknesses.append("Architecture needs organization")
                before_resume.append("Organize project structure with clear separation of concerns")
            arch_earned = round(3 + (arch_pct / 100.0) * 12)
            
        total_earned += arch_earned
        evidence.append(f"Architecture contribution: {arch_earned}/{arch_max}")
    else:
        excluded_dimensions.append("Architecture")
        
    if is_sec_applicable:
        sec_earned = 0
        sec_max = 10
        total_max += sec_max
        applicable_signals.append("Security")
        
        sec_dim = next((d for d in engineering_dimensions if d.get('id') == "security"), None)
        if sec_dim:
            sec_pct = (sec_dim['score'] / sec_dim['maxScore']) * 100 if sec_dim.get('maxScore', 0) > 0 else 0
            if sec_pct >= 70:
                strengths.append("Good security hygiene")
            elif sec_pct < 50:
                weaknesses.append("Security hygiene needs improvement")
                before_resume.append("Address security findings and add security documentation")
            sec_earned = round((sec_pct / 100.0) * 10)
            
        total_earned += sec_earned
        evidence.append(f"Security contribution: {sec_earned}/{sec_max}")
    else:
        excluded_dimensions.append("Security")
        
    pres_earned = 0
    pres_max = 10
    total_max += pres_max
    applicable_signals.append("Presentation")
    
    if raw_metrics.get('hasCI'):
        pres_earned += 3
        strengths.append("CI/CD pipeline configured")
        
    if raw_metrics.get('hasDeployment'):
        pres_earned += 4
        strengths.append("Deployment evidence present")
        
    if raw_metrics.get('hasLicense'):
        pres_earned += 3
    else:
        weaknesses.append("No license")
        before_resume.append("Add a license file")
        
    total_earned += pres_earned
    evidence.append(f"Presentation contribution: {pres_earned}/{pres_max}")
    
    comm_earned = 0
    comm_max = 5
    total_max += comm_max
    applicable_signals.append("Community")
    
    if raw_metrics.get('hasContributing'):
        comm_earned += 2
        
    if raw_metrics.get('contributorCount', 0) > 1:
        comm_earned += 2
        
    if raw_metrics.get('recentActivity'):
        comm_earned += 1
        
    total_earned += comm_earned
    evidence.append(f"Community contribution: {comm_earned}/{comm_max}")
    
    score = 0
    if total_max > 0:
        score = round((total_earned / total_max) * 100)
        
    score = max(0, min(100, round(score)))
    
    methodology.append(f"Normalized portfolio score based on {len(applicable_signals)} applicable dimension(s)")
    methodology.append(f"Total earned points: {total_earned} / {total_max}")
    if excluded_dimensions:
        methodology.append(f"Excluded dimensions due to {classification.get('type')} profile: {', '.join(excluded_dimensions)}")
        
    status = get_resume_readiness_status(score)
    summary = ""
    if score >= 80:
        summary = "Strong project! Well-documented, organized, and demonstrates solid engineering practices."
    elif score >= 60:
        summary = "Good project, but missing a few key elements before it stands out on a resume."
    elif score >= 40:
        summary = "Decent project, but needs work before it's ready for a portfolio."
    else:
        summary = "This project is missing fundamental documentation and structure."
        
    return {
        "score": score,
        "status": status,
        "summary": summary,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "beforeResume": before_resume,
        "applicableSignals": applicable_signals,
        "excludedDimensions": excluded_dimensions,
        "evidence": evidence,
        "methodology": methodology
    }
