# Repo Rizz — Scoring System

## Overview

Repo Rizz uses deterministic, evidence-based scoring across 9 dimensions. Each dimension contributes to an overall health score using configurable weights.

## Dimensions & Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Code Quality | 15% | Linting, formatting, TypeScript, file organization |
| Security | 15% | Secrets, .env, security docs, CI security, dependency safety |
| Documentation | 10% | README quality, LICENSE, CONTRIBUTING, CHANGELOG |
| Testing | 10% | Test files, frameworks, CI test workflows |
| Architecture | 10% | Directory structure, deployment config, separation of concerns |
| Maintainability | 10% | CI/CD, dependency management, templates, contribution docs |
| Activity | 10% | Commits, issues, PRs, repository freshness |
| Community | 10% | Stars, forks, contributors, topics, license |
| Resume Readiness | 10% | Composite of other dimensions |

## Score Ranges

| Score | Status | Meaning |
|-------|--------|---------|
| 80-100 | STRONG | Excellent engineering practices |
| 60-79 | GOOD | Solid foundation, minor improvements needed |
| 40-59 | FAIR | Workable but significant gaps |
| 0-39 | WEAK | Major improvements required |

## Health Score Calculation

```
Health Score = Σ (Dimension Score × Dimension Weight) / Σ Weights
```

## Scoring Principles

1. **Evidence-based** — Every score backed by concrete findings
2. **Deterministic** — Same input produces same score
3. **Transparent** — All evidence visible to user
4. **Fair** — Personal projects not penalized for low stars
5. **Actionable** — Low scores come with specific recommendations

## Resume Readiness

Calculated from other dimensions. Considers:
- CI/CD presence
- Documentation quality
- Test coverage
- Architecture clarity
- Activity level
- Security practices
