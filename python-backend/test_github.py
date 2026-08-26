import pytest
import httpx
from github import get_github_headers, GitHubRateLimitError, handle_response
import os

def test_token_configured(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "dummy_token")
    headers = get_github_headers()
    assert headers["Authorization"] == "Bearer dummy_token"
    assert "User-Agent" in headers

def test_token_missing(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    headers = get_github_headers()
    assert "Authorization" not in headers
    assert "User-Agent" in headers

@pytest.mark.asyncio
async def test_403_rate_limit():
    resp = httpx.Response(403, headers={"X-RateLimit-Remaining": "0"}, request=httpx.Request("GET", "https://api.github.com"))
    with pytest.raises(GitHubRateLimitError):
        await handle_response(resp)

@pytest.mark.asyncio
async def test_404_not_found():
    from github import GitHubNotFoundError
    resp = httpx.Response(404, request=httpx.Request("GET", "https://api.github.com"))
    with pytest.raises(GitHubNotFoundError):
        await handle_response(resp)

@pytest.mark.asyncio
async def test_network_failure():
    from github import GitHubNetworkError
    assert issubclass(GitHubNetworkError, Exception)

