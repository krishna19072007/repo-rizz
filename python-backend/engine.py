import time
from datetime import datetime
from ai import AIProvider
from scoring import classify_repository, calculate_repository_score, calculate_resume_readiness
from analyzers import analyze_architecture, analyze_code_quality, analyze_documentation, analyze_security, analyze_testing

async def run_analysis(input_data: dict) -> dict:
    start_time = time.time()
    all_limitations = []

    # 1. Classification
    classification = classify_repository(input_data)
    input_data["classification"] = classification
    
    # Run analyzers
    testing_dim = analyze_testing(input_data)
    dimensions = [
        analyze_documentation(input_data),
        analyze_code_quality(input_data),
        analyze_architecture(input_data),
        analyze_security(input_data),
    ]

    # Add to input_data so scoring.py can find it
    input_data["dimension_scores"] = dimensions
    
    # 2. Base Dimensions
    scoring_result = calculate_repository_score(input_data)
    all_dimensions = scoring_result["dimensions"]
    raw_metrics_combined = {}
    for d in all_dimensions: raw_metrics_combined.update(d.get('rawMetrics', {}))
    raw_metrics_combined.update(testing_dim.get('rawMetrics', {}))
    
    # Ensure hasTests fallback is explicitly mapped
    if not raw_metrics_combined.get('hasTests') and raw_metrics_combined.get('testFileCount', 0) > 0:
        raw_metrics_combined['hasTests'] = True
        
    for d in all_dimensions:
        all_limitations.extend(d.get("limitations", []))

    # 3. Resume Readiness
    rr_result = calculate_resume_readiness(all_dimensions, raw_metrics_combined, classification)
    
    resume_readiness_dimension = {
        "id": "resumeReadiness",
        "name": "Resume Readiness",
        "score": rr_result["score"],
        "maxScore": 100,
        "weight": 100,
        "findings": [],
        "evidence": rr_result["evidence"],
        "summary": rr_result["summary"],
        "recommendation": None,
        "rawMetrics": {},
        "rulesApplied": rr_result.get("methodology", []),
        "limitations": rr_result.get("excludedDimensions", []) + ["Resume Readiness is a synthesized score — not a direct engineering measurement"],
        "confidence": 1.0,
        "confidenceReason": "Deterministic calculation"
    }

    # 4. AI Enhancements
    ai_summary = None
    ai_rizz_verdict = None
    ai_unavailable = True
    ai_provider = AIProvider()

    repo_info = {
        "owner": input_data.get("repo", {}).get("owner", {}).get("login"),
        "name": input_data.get("repo", {}).get("name"),
        "fullName": input_data.get("repo", {}).get("full_name"), "description": input_data.get("repo", {}).get("description"),
        "description": input_data.get("repo", {}).get("description"),
        "url": input_data.get("repo", {}).get("html_url"),
        "defaultBranch": input_data.get("repo", {}).get("default_branch"),
        "stars": input_data.get("repo", {}).get("stargazers_count"),
    }

    import asyncio
    try:
        summary_task = asyncio.create_task(ai_provider.generate_summary(repo_info, all_dimensions))
        verdict_task = asyncio.create_task(ai_provider.generate_rizz_verdict(repo_info, classification, all_dimensions))
        
        await asyncio.wait([summary_task, verdict_task])
        
        summary_val = summary_task.result() if not summary_task.exception() else None
        verdict_val = verdict_task.result() if not verdict_task.exception() else None

        if summary_val and "unavailable" not in summary_val:
            ai_summary = summary_val
            ai_unavailable = False
        if verdict_val and "unavailable" not in verdict_val:
            ai_rizz_verdict = verdict_val
    except Exception as e:
        print(f"[AI] Error: {e}")

    # 5. Build Final Output
    all_findings = []
    for d in all_dimensions:
        all_findings.extend(d.get("findings", []))
    
    critical_findings = [f for f in all_findings if f.get("severity") == "critical"]
    
    recommendations = []
    for f in critical_findings:
        recommendations.append({
            "id": f.get("id"),
            "priority": "critical",
            "category": f.get("dimension", "General").title(),
            "title": f"Fix {f.get('message', 'Issue')}",
            "description": f.get("description"),
            "impact": "+10 points"
        })

    all_limitations.append(f"Repository type: {classification['type']} (confidence: {int(classification['confidence'] * 100)}%)")

    return {
        "id": f"analysis_{int(time.time())}",
        "repository": repo_info,
        "resumeReadinessScore": rr_result["score"],
        "resumeReadinessStatus": rr_result.get("status", "notReady"),
        "resumeReadinessSummary": rr_result.get("summary", ""),
        "resumeReadinessStrengths": rr_result.get("strengths", []),
        "resumeReadinessWeaknesses": rr_result.get("weaknesses", []),
        "resumeReadinessBeforeResume": rr_result.get("beforeResume", []),
        "resumeReadinessTotalEarned": rr_result.get("totalEarned", 0),
        "resumeReadinessTotalMax": rr_result.get("totalMax", 0),
        "resumeReadinessBreakdown": rr_result.get("breakdown", {}),
        "engineeringDimensions": all_dimensions,
        "resumeReadinessDimension": resume_readiness_dimension,
        "dimensions": all_dimensions + [resume_readiness_dimension],
        "rizzVerdict": ai_rizz_verdict or "Solid project.",
        "criticalFindings": critical_findings,
        "recommendations": recommendations,
        "aiSummary": ai_summary,
        "aiRizzVerdict": ai_rizz_verdict,
        "aiUnavailable": ai_unavailable,
        "analyzedAt": datetime.utcnow().isoformat() + "Z",
        "analysisTimeMs": int((time.time() - start_time) * 1000),
        "limitations": all_limitations,
        "repositoryType": classification,
        "applicableDimensions": scoring_result.get("applicableCount", 0),
        "notApplicableDimensions": scoring_result.get("notApplicableCount", 0),
        "scoringVersion": scoring_result.get("scoringVersion", "3.1"),
        "weightedContributions": scoring_result.get("weightedContributions", [])
    }
