# Repo Rizz — Product Requirements Document

## Problem

Developers struggle to evaluate the engineering health of GitHub repositories objectively. Whether reviewing open source projects, evaluating potential employers, or assessing their own work, there's no single tool that provides a comprehensive, evidence-based health report.

## Target Users

- **Developers** evaluating repositories for contribution
- **Job seekers** wanting to showcase their best work
- **Tech leads** assessing codebases before adoption
- **Students** learning what good engineering looks like
- **Open source maintainers** wanting to improve their projects

## Goals

1. Analyze any public GitHub repository
2. Score across 9 engineering dimensions
3. Provide evidence-based findings
4. Generate actionable recommendations
5. Assess resume readiness
6. Work without paid infrastructure
7. Optional AI enhancement via Gemini

## Non-Goals

- Private repository analysis (MVP)
- Real-time code execution
- Enterprise static analysis
- CI/CD integration (MVP)

## Core Features

1. **Repository Analysis** — Fetch and analyze GitHub data
2. **9-Dimension Scoring** — Code Quality, Security, Documentation, Testing, Architecture, Maintainability, Activity, Community, Resume Readiness
3. **Repo Fingerprint** — Unique visual representation
4. **Findings & Recommendations** — Evidence-based insights
5. **Resume Readiness** — Portfolio-ready assessment
6. **Rizz Verdict** — Fun, data-driven summary
7. **Demo Mode** — Showcase with fixture data

## MVP

- Landing page with 3D visual
- Repository URL input
- Live analysis pipeline
- Results with all 9 dimensions
- Resume readiness score
- Rizz verdict
- Demo mode
- Mobile responsive

## Future Roadmap

- Repository comparison
- Analysis history (Supabase)
- Before/after tracking
- Authentication
- Custom scoring weights
- Export as PDF
- Slack/webhook notifications
- Team analytics

## Success Metrics

- Analysis completion rate > 95%
- Page load < 3s
- Mobile usability score > 90
- User can understand findings without developer background
