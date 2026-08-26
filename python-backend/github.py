import os
import httpx
import base64
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

class GitHubRateLimitError(Exception):
    pass

class GitHubNotFoundError(Exception):
    pass

class GitHubServiceError(Exception):
    pass

class GitHubNetworkError(Exception):
    pass

def get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Repo-Rizz-Analyzer/1.0"
    }
    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"
    return headers

async def handle_response(resp: httpx.Response):
    if resp.status_code == 200:
        return resp.json()
    if resp.status_code == 404:
        raise GitHubNotFoundError(f"Repository not found.")
    if resp.status_code in (403, 429):
        # 403 can be rate limit or secondary rate limit or permissions
        # rate limits usually have X-RateLimit-Remaining == "0"
        limit_remaining = resp.headers.get("X-RateLimit-Remaining")
        if limit_remaining == "0" or resp.status_code == 429 or "rate limit" in resp.text.lower():
            raise GitHubRateLimitError("GitHub API rate limit exceeded. Configure a GitHub token or try again later.")
        raise GitHubServiceError(f"GitHub API forbidden: {resp.text}")
    if resp.status_code >= 500:
        raise GitHubServiceError(f"GitHub service error: {resp.status_code}")
    
    # other non-200
    resp.raise_for_status()

async def safe_request(client: httpx.AsyncClient, url: str, return_empty_on_error: bool = False):
    try:
        resp = await client.get(url)
        return await handle_response(resp)
    except httpx.RequestError:
        if return_empty_on_error: return None
        raise GitHubNetworkError("GitHub unavailable due to network timeout or error.")
    except (GitHubRateLimitError, GitHubNotFoundError, GitHubServiceError, GitHubNetworkError):
        raise
    except httpx.HTTPStatusError as e:
        if return_empty_on_error: return None
        raise GitHubServiceError(f"HTTP error: {e}")

async def get_repo(owner: str, name: str, client: httpx.AsyncClient):
    return await safe_request(client, f"https://api.github.com/repos/{owner}/{name}")

async def get_languages(owner: str, name: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/languages", True)
    return data if data else {}

async def get_commits(owner: str, name: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/commits?per_page=30", True)
    return data if isinstance(data, list) else []

async def get_issues(owner: str, name: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/issues?per_page=30", True)
    return data if isinstance(data, list) else []

async def get_pull_requests(owner: str, name: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/pulls?per_page=30", True)
    return data if isinstance(data, list) else []

async def get_workflows(owner: str, name: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/actions/workflows", True)
    if data and isinstance(data, dict):
        return data.get("workflows", [])
    return []

async def get_contributors(owner: str, name: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/contributors?per_page=30", True)
    return data if isinstance(data, list) else []

async def get_repo_tree(owner: str, name: str, branch: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/git/trees/{branch}?recursive=1", True)
    if data and isinstance(data, dict):
        return data.get("tree", [])
    return []

async def get_file_content(owner: str, name: str, path: str, client: httpx.AsyncClient):
    data = await safe_request(client, f"https://api.github.com/repos/{owner}/{name}/contents/{path}", True)
    if data and isinstance(data, dict) and data.get("encoding") == "base64":
        return base64.b64decode(data["content"]).decode("utf-8")
    return None

async def fetch_analysis_input(owner: str, name: str):
    headers = get_github_headers()
    
    # 1. Reuse connection and metadata
    async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
        # Fetch repo first to ensure it exists before spamming parallel requests
        repo = await get_repo(owner, name, client)
        branch = repo.get("default_branch", "main")
        
        # Parallel data fetch
        tasks = await asyncio.gather(
            get_languages(owner, name, client),
            get_commits(owner, name, client),
            get_issues(owner, name, client),
            get_pull_requests(owner, name, client),
            get_workflows(owner, name, client),
            get_contributors(owner, name, client),
            get_repo_tree(owner, name, branch, client),
            return_exceptions=True
        )
        
        # Check if any tasks failed with rate limit/auth
        for task in tasks:
            if isinstance(task, GitHubRateLimitError) or isinstance(task, GitHubServiceError):
                raise task

        languages, commits, issues, pulls, workflows, contributors, tree = [
            t if not isinstance(t, Exception) else ([] if i != 0 else {}) 
            for i, t in enumerate(tasks)
        ]

        async def get_file_variants(*paths):
            for p in paths:
                # We can optimize by looking into `tree` before fetching!
                # If tree is populated, only fetch if path exists in tree
                if tree and isinstance(tree, list):
                    found = False
                    for item in tree:
                        if item.get("path", "").lower() == p.lower():
                            found = True
                            p_actual = item.get("path")
                            break
                    if not found:
                        continue
                    # Fetch using actual case
                    content = await get_file_content(owner, name, p_actual, client)
                    if content: return content
                else:
                    content = await get_file_content(owner, name, p, client)
                    if content: return content
            return None

        async def get_json_variants(*paths):
            for p in paths:
                if tree and isinstance(tree, list):
                    if not any(item.get("path", "").lower() == p.lower() for item in tree):
                        continue
                content = await get_file_content(owner, name, p, client)
                if content: 
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return None
            return None

        readme, license, contributing, security, changelog, codeowners, pkg_json = await asyncio.gather(
            get_file_variants("README.md", "readme.md", "Readme.md"),
            get_file_variants("LICENSE", "LICENSE.md", "license.md", "LICENCE", "COPYING"),
            get_file_variants("CONTRIBUTING.md", "contributing.md", "CONTRIBUTING", "contributing"),
            get_file_variants("SECURITY.md", "security.md"),
            get_file_variants("CHANGELOG.md", "changelog.md", "CHANGES.md", "HISTORY.md"),
            get_file_variants("CODEOWNERS", ".github/CODEOWNERS"),
            get_json_variants("package.json"),
        )

        return {
            "repo": repo,
            "languages": languages,
            "commits": commits,
            "issues": issues,
            "pullRequests": pulls,
            "workflows": workflows,
            "contributors": contributors,
            "tree": tree,
            "readme": readme,
            "license": license,
            "contributing": contributing,
            "security": security,
            "changelog": changelog,
            "codeowners": codeowners,
            "packageJson": pkg_json
        }
