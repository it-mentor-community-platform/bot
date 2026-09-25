import logging
import base64
from urllib.parse import urlparse

from requests import Response
from requests.exceptions import RequestException
from requests_ratelimiter import BucketFullException, LimiterSession

from src.config.env import INTERVIEW_PREP_SITE_REPO_OWNER
from src.config.env import INTERVIEW_PREP_SITE_REPO_NAME
from src.config.env import GITHUB_COMMUNITY_BOT_ACCESS_TOKEN

BASE_API_URL = "https://api.github.com"
OWNER = INTERVIEW_PREP_SITE_REPO_OWNER
REPO = INTERVIEW_PREP_SITE_REPO_NAME
ACCESS_TOKEN = GITHUB_COMMUNITY_BOT_ACCESS_TOKEN


headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "it-mentor-community-bot",
    "Content-Type": "application/json",
}

session = LimiterSession(per_hour=5000, max_delay=0)

log = logging.getLogger(__name__)


def is_github_repository_url(repository_url: str) -> bool:
    return urlparse(repository_url).hostname in {"github.com", "www.github.com"}


def is_repository_available(repository_url: str) -> bool | None:
    if not is_github_repository_url(repository_url):
        return False

    parsed_url = urlparse(repository_url)
    path_parts = parsed_url.path.strip("/").split("/")

    if len(path_parts) != 2:
        return False

    owner, repo = path_parts

    if not owner or not repo:
        return False

    api_url = f"{BASE_API_URL}/repos/{owner}/{repo}"

    try:
        response = session.get(api_url, headers=headers, timeout=5)
    except (RequestException, BucketFullException) as e:
        log.error("Failed to check GitHub repository '%s/%s': %s", owner, repo, e)
        return None

    if response.status_code == 404:
        return False

    if response.status_code != 200:
        log.error(
            "GitHub returned %s while checking '%s/%s'",
            response.status_code,
            owner,
            repo,
        )
        return None

    try:
        response_body: dict[str, object] = response.json()
        is_private = response_body.get("private")

        if not isinstance(is_private, bool):
            log.error("Invalid GitHub response for '%s/%s'", owner, repo)
            return None

        return not is_private
    except (AttributeError, ValueError):
        log.error("Invalid GitHub response for '%s/%s'", owner, repo)
        return None


def get_file_content(
    path: str, repo: str = REPO, owner: str = OWNER
) -> tuple[str, str] | None:
    log.info(f"Getting content of the '{path}' file")

    try:
        if path.startswith("/"):
            path = path[1:]

        url = f"{BASE_API_URL}/repos/{owner}/{repo}/contents/{path}"

        response = session.get(url, headers=headers)

        if response.status_code != 200:
            log.warning(
                f"GitHub returned status code {response.status_code} & message: '{_get_message(response)}' for read file '{path}' content request"
            )
            return None

        json_response = response.json()

        file_content = base64.b64decode(json_response["content"]).decode()
        file_sha = json_response["sha"]

        return (file_content, file_sha)

    except BucketFullException:
        log.error(f"Rate limit for GitHub API exceeded, cannot read '{path}' content")
        return None


def update_file_content(
    sha: str,
    path: str,
    content: str,
    branch: str,
    commit_message: str,
    repo: str = REPO,
    owner: str = OWNER,
) -> bool:
    log.info(f"Updating '{path}' file content in the {branch} branch")

    try:
        if path.startswith("/"):
            path = path[1:]

        url = f"{BASE_API_URL}/repos/{owner}/{repo}/contents/{path}"

        request_body = {
            "message": commit_message,
            "content": _base64_encode(content),
            "sha": sha,
            "branch": branch,
        }

        response = session.put(url, headers=headers, json=request_body)

        if response.status_code != 200:
            log.warning(
                f"GitHub returned status code {response.status_code} & message: '{_get_message(response)}' for update file '{path}' content request"
            )
            return False

        return True

    except BucketFullException:
        log.error(f"Rate limit for GitHub API exceeded, cannot update '{path}' content")
        return False


def get_last_commit_sha_of_branch(
    branch: str,
    repo: str = REPO,
    owner: str = OWNER,
) -> str | None:
    log.info(f"Getting info of {branch} branch")

    try:
        url = f"{BASE_API_URL}/repos/{owner}/{repo}/git/refs/heads/{branch}"

        response = session.get(url, headers=headers)

        if response.status_code != 200:
            log.warning(
                f"GitHub returned status code {response.status_code} & message: '{_get_message(response)}' for getting info about {branch} branch"
            )
            return None

        return response.json()["object"]["sha"]

    except BucketFullException:
        log.error(
            f"Rate limit for GitHub API exceeded, cannot get {branch} branch info"
        )
        return None


def create_branch(
    branch: str,
    parent_sha: str,
    repo: str = REPO,
    owner: str = OWNER,
) -> bool:
    log.info(f"Creating branch {branch} with parent commit {parent_sha}")

    try:
        url = f"{BASE_API_URL}/repos/{owner}/{repo}/git/refs"

        request_body = {
            "ref": f"refs/heads/{branch}",
            "sha": parent_sha,
        }

        response = session.post(url, headers=headers, json=request_body)

        if response.status_code != 201:
            log.warning(
                f"GitHub returned status code {response.status_code} & message: '{_get_message(response)}' for creating new branch {branch}"
            )
            return False

        return True

    except BucketFullException:
        log.error(f"Rate limit for GitHub API exceeded, cannot create {branch} branch")
        return False


def create_pull_request(
    head: str,
    base: str,
    title: str,
    body: str | None,
    repo: str = REPO,
    owner: str = OWNER,
) -> str | None:
    log.info(f"Creating pull request from {head} to {base} with title: {title}")

    try:
        url = f"{BASE_API_URL}/repos/{owner}/{repo}/pulls"

        request_body = {
            "title": title,
            "head": head,
            "base": base,
        }

        if body is not None:
            request_body["body"] = body

        response = session.post(url, headers=headers, json=request_body)

        if response.status_code != 201:
            log.warning(
                f"GitHub returned status code {response.status_code} & message: '{_get_message(response)}' for creating pull request from {head} to {base}"
            )
            return None

        return response.json()["html_url"]

    except BucketFullException:
        log.error(
            f"Rate limit for GitHub API exceeded, cannot create pull request from {head} to {base}"
        )
        return None


def _base64_encode(content: str) -> str:
    content_bytes = content.encode("utf-8")
    base64_bytes = base64.b64encode(content_bytes)
    return base64_bytes.decode("utf-8")


def _get_message(response: Response) -> str:
    json_response = response.json()
    return json_response.get("message")
