"""Unit tests for the GitHub URL normalization contract (issue #85)."""

import pytest

from src.handler.util import normalize_github_repository_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("github.com/Totsamyq/Simulation", "https://github.com/Totsamyq/Simulation"),
        (
            "https://github.com/Totsamyq/Simulation.git",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "https://github.com/Totsamyq/Simulation/tree/main",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "https://github.com/Totsamyq/Simulation/blob/main/README.md",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "https://github.com/Totsamyq/Simulation/issues/1",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "https://github.com/Totsamyq/Simulation/?tab=readme#intro",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "www.github.com/Totsamyq/Simulation.git/",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "HTTPS://GITHUB.COM/Totsamyq/Simulation",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "  https://github.com/Totsamyq/Simulation  ",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "github.com/Totsamyq/Simulation.git",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "github.com/Totsamyq/Simulation/tree/feature/new-ui",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "https://github.com/Totsamyq/Simulation/pull/123",
            "https://github.com/Totsamyq/Simulation",
        ),
        (
            "https://github.com/user/repo_name.v2",
            "https://github.com/user/repo_name.v2",
        ),
        (
            "https://github.com:443/user/repo",
            "https://github.com/user/repo",
        ),
        (
            "https://user@github.com/user/repo",
            "https://github.com/user/repo",
        ),
        (
            "https://github.com/or\ng/repo",
            "https://github.com/org/repo",
        ),
        (
            "https://github.com/u\tser/repo",
            "https://github.com/user/repo",
        ),
        (
            "https://github.com/user/re\rpo",
            "https://github.com/user/repo",
        ),
    ],
)
def test_canonical_github_repository_url(raw: str, expected: str) -> None:
    assert normalize_github_repository_url(raw) == expected
    assert normalize_github_repository_url(expected) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "github.com",
        "github.com/user",
        "github.com/user/",
        "https://github.com/user/.git",
        "https://github.com.evil.test/user/repo",
        "https://notgithub.com/user/repo",
        "https://example.org/user/repo?source=github.com",
        "https://gitlab.com/user/repo",
        "http://github.com/user/repo",
        "git@github.com:user/repo.git",
        "ftp://github.com/user/repo",
        "https://github.com@evil.com/user/repo",
    ],
)
def test_invalid_github_repository_url(raw: str) -> None:
    with pytest.raises(ValueError):
        normalize_github_repository_url(raw)
