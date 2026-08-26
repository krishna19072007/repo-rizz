# Repo Rizz — Security

## API Key Security

### GitHub Token
- Stored server-side only (environment variable)
- Never sent to client
- Used for higher rate limits only

### Gemini API Key
- Stored server-side only
- Never exposed in client bundles
- Optional — core functionality works without it

## Input Validation

### Repository URLs
- Parsed and validated with regex
- Only GitHub URLs accepted
- Owner/repo format enforced
- No path traversal possible

### API Requests
- Content-Type validation
- Request body size limits
- Timeout protection

## Repository Safety

**NEVER** execute code from analyzed repositories:
- No `npm install` on untrusted repos
- No script execution
- No dynamic code evaluation
- Repository treated as read-only data

## Rate Limits

- GitHub API: 60 requests/hour (unauthenticated)
- GitHub API: 5,000 requests/hour (authenticated)
- Graceful degradation when limits reached

## Secret Detection

Repo Rizz detects potential secrets:
- .env files in repository
- Suspicious configuration files
- Reports findings without exposing content

## AI Safety

- Structured prompts prevent prompt injection
- AI receives sanitized data only
- AI output not executed or stored as code
- Graceful fallback when AI unavailable
