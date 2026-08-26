const fs = require('fs');
let code = fs.readFileSync('python-backend/analyzers.py', 'utf8');

code = code.replace(/def create_finding[\s\S]*?return \{[\s\S]*?\}/, `def create_finding(id: str, severity: str, dimension: str, message: str, description: str, files=None, snippet=None, recommendation=None):
    return {
        "id": id,
        "severity": severity,
        "dimension": dimension,
        "message": message,
        "description": description,
        "files": files or [],
        "snippet": snippet,
        "recommendation": recommendation
    }`);

code = code.replace(/def create_dimension[\s\S]*?return \{[\s\S]*?\}/, `def create_dimension(dimension, dimensionName, score, maxScore, weight, findings, evidence, summary, recommendation, rawMetrics, rulesApplied, limitations, confidence, confidenceReason):
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
    }`);

fs.writeFileSync('python-backend/analyzers.py', code);
