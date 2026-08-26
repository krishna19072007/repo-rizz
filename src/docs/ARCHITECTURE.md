# Repo Rizz — Architecture

## Overview

Next.js 16 App Router application with TypeScript, Tailwind CSS, and modular analysis engine.

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│  API Routes  │────▶│   GitHub    │
│  (Next.js)   │     │  (Server)    │     │    API      │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  Analysis   │
                    │   Engine    │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │   Scoring   │
                    │   Engine    │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  AI Layer   │
                    │  (Optional) │
                    └─────────────┘
```

## Layers

### Frontend
- Next.js 16 App Router
- TypeScript
- Tailwind CSS
- Framer Motion (animations)
- React Three Fiber (3D)

### API Layer
- `/api/github/analyze` — Main analysis endpoint
- `/api/ai/*` — AI-powered insights (optional)

### Analysis Engine
- Modular dimension analyzers
- Deterministic scoring
- Evidence collection
- Recommendation generation

### GitHub Integration
- REST API v3
- Rate limit handling
- Token-based auth (optional)
- Caching via Next.js revalidation

### AI Layer
- Provider abstraction pattern
- Gemini integration
- Structured prompts
- Graceful degradation

### Database (Optional)
- Supabase PostgreSQL
- Analysis history
- Saved repositories

## Security Boundaries

- Never execute repository code
- Treat all repo contents as untrusted input
- API keys stored server-side only
- Rate limiting respected
- No SSRF vulnerabilities
