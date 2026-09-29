"""Copilot SDK PR reviewer for Azure DevOps.

The starter is intentionally incomplete in four lesson areas: real per-file diffs,
deny-by-default permissions, severity gating, and idempotent PR comments. It is
still runnable and safe: ``--dry-run`` is fully offline and needs no credentials.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import os
import sys
import textwrap
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:  # Tests run without the SDK installed; live runs use the real package.
    from copilot import CopilotClient
    from copilot.session import PermissionHandler
except ImportError:  # pragma: no cover - exercised only when dependency is absent.
    CopilotClient = None  # type: ignore[assignment]

    class PermissionHandler:  # type: ignore[no-redef]
        approve_all = object()


API = "https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}"
API_VERSION = "7.1"
DEFAULT_ORG = "azultechlab"
DEFAULT_PROJECT = "Copilot-Hackathon"
DEFAULT_REPO = "hack04-copilot-sdk-ado-review"
DEFAULT_SAMPLE_DIFF = Path("samples/sample_diff.patch")
# send_and_wait's own default is 60s, which a real multi-KB diff review exceeds.
REVIEW_TIMEOUT_SECONDS = 900.0

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are a senior staff engineer doing a pull request review.

    Review ONLY the diff you are given. Do not invent files or lines.

    Priorities, in order:
      1. Security - injection, secrets in code, authn/authz gaps, unsafe paths.
      2. Correctness - logic errors, unhandled errors, race conditions, None handling.
      3. Performance - O(n^2) loops, unbounded work, repeated network calls.
      4. Maintainability - only when it blocks safe operation.

    Follow AGENTS.md from the working directory. Emit the Markdown sections it requires,
    including the fenced JSON machine-findings block.
    """
).strip()

SKIP_EXACT = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock"}
SKIP_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".min.js",
    ".min.css",
}
SKIP_PARTS = {"node_modules", "dist", "build", "vendor", "generated", "__pycache__"}


@dataclass(frozen=True)
class Credential:
    scheme: str
    token: str


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copilot SDK PR reviewer for Azure DevOps")
    parser.add_argument("--org", default=DEFAULT_ORG)
    parser.add_argument("--project", default=DEFAULT_PROJECT)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--pr", type=int)
    parser.add_argument(
        "--model", default="claude-sonnet-4.5", choices=["gpt-5", "claude-sonnet-4.5", "auto"]
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the prompt using the bundled sample diff and exit",
    )
    parser.add_argument("--sample-diff", type=Path, default=DEFAULT_SAMPLE_DIFF)
    parser.add_argument("--timeout", type=float, default=REVIEW_TIMEOUT_SECONDS)
    return parser.parse_args(argv)


def org_from_collection_uri(value: str) -> str:
    trimmed = value.rstrip("/")
    if trimmed.startswith("https://dev.azure.com/"):
        return trimmed.removeprefix("https://dev.azure.com/").split("/", 1)[0]
    return trimmed.rsplit("/", 1)[-1]


def credential_from_env(env: dict[str, str] | None = None) -> Credential | None:
    source = env if env is not None else os.environ
    system_token = source.get("SYSTEM_ACCESSTOKEN")
    if system_token:
        return Credential("Bearer", system_token)
    pat = source.get("AZURE_DEVOPS_PAT")
    if pat:
        encoded = base64.b64encode(f":{pat}".encode()).decode()
        return Credential("Basic", encoded)
    return None


def ado_headers(credential: Credential) -> dict[str, str]:
    return {
        "Authorization": f"{credential.scheme} {credential.token}",
        "Content-Type": "application/json",
    }


def should_skip_diff_file(path: str) -> bool:
    normalised = path.replace("\\", "/").lstrip("/")
    name = normalised.rsplit("/", 1)[-1].lower()
    parts = {part.lower() for part in normalised.split("/")}
    return (
        name in SKIP_EXACT
        or any(name.endswith(suffix) for suffix in SKIP_SUFFIXES)
        or bool(parts & SKIP_PARTS)
    )


def api_base(org: str, project: str, repo: str) -> str:
    return API.format(
        org=urllib.parse.quote(org, safe=""),
        project=urllib.parse.quote(project, safe=""),
        repo=urllib.parse.quote(repo, safe=""),
    )


def get_pr_diff(org: str, project: str, repo: str, pr: int, credential: Credential) -> str:
    """Starter implementation: changed files plus truncated full content, not true hunks."""
    base = api_base(org, project, repo)
    headers = ado_headers(credential)
    import requests

    pr_meta = requests.get(
        f"{base}/pullrequests/{pr}",
        headers=headers,
        params={"api-version": API_VERSION},
        timeout=60,
    )
    pr_meta.raise_for_status()
    meta = pr_meta.json()
    source = meta["lastMergeSourceCommit"]["commitId"]
    target = meta["lastMergeTargetCommit"]["commitId"]
    changes_response = requests.get(
        f"{base}/diffs/commits",
        headers=headers,
        params={
            "api-version": API_VERSION,
            "baseVersion": target,
            "baseVersionType": "commit",
            "targetVersion": source,
            "targetVersionType": "commit",
        },
        timeout=60,
    )
    changes_response.raise_for_status()
    changes = changes_response.json()
    chunks = [f"# PR {pr}: {meta.get('title', '')}\n{meta.get('description', '') or ''}\n"]
    for change in changes.get("changes", []):
        item = change.get("item", {})
        path = item.get("path")
        if not path or item.get("isFolder") or should_skip_diff_file(path):
            continue
        body_response = requests.get(
            f"{base}/items",
            headers=headers,
            params={
                "api-version": API_VERSION,
                "path": path,
                "versionDescriptor.version": source,
                "versionDescriptor.versionType": "commit",
                "includeContent": "true",
                "$format": "text",
            },
            timeout=60,
        )
        body_response.raise_for_status()
        chunks.append(
            f"\n### {change.get('changeType')} {path}\n```\n{body_response.text[:20000]}\n```"
        )
    return "\n".join(chunks)


def load_diff_for_args(args: argparse.Namespace) -> str:
    if args.dry_run:
        return args.sample_diff.read_text(encoding="utf-8")
    if args.pr is None:
        raise ValueError("--pr is required unless --dry-run is used")
    credential = credential_from_env()
    if credential is None:
        raise RuntimeError("Missing SYSTEM_ACCESSTOKEN or AZURE_DEVOPS_PAT")
    return get_pr_diff(args.org, args.project, args.repo, args.pr, credential)


def build_review_prompt(diff: str) -> str:
    return f"Review this pull request.\n\n{diff}"


def reply_text(reply: Any) -> str:
    """Pull the assistant text out of a SessionEvent.

    send_and_wait returns a SessionEvent, whose payload lives in `.data`; the
    event itself has no `.content`. A naive getattr(reply, "content", reply)
    silently stringifies the whole event and posts that as the PR comment.
    """
    if reply is None:
        return ""
    data = getattr(reply, "data", None)
    content = getattr(data, "content", None)
    if content is None and isinstance(data, dict):
        content = data.get("content")
    if content is None:
        content = getattr(reply, "content", None)
    if content is None:
        raise RuntimeError(
            f"Copilot returned no assistant message (event type: {getattr(reply, 'type', '?')})"
        )
    return str(content).strip()


async def review(diff: str, model: str, timeout: float = REVIEW_TIMEOUT_SECONDS) -> str:
    if CopilotClient is None:
        raise RuntimeError("github-copilot-sdk is not installed")
    async with CopilotClient(working_directory=os.getcwd()) as client:  # type: ignore[misc]  # noqa: SIM117
        async with await client.create_session(
            model=model,
            on_permission_request=PermissionHandler.approve_all,
            system_message={"mode": "append", "content": SYSTEM_PROMPT},
        ) as session:
            # send_and_wait defaults to 60s and raises TimeoutError; a real review
            # over a multi-KB diff routinely takes longer than that.
            reply = await session.send_and_wait(build_review_prompt(diff), timeout=timeout)
    return reply_text(reply)


def post_pr_comment(
    org: str, project: str, repo: str, pr: int, credential: Credential, text: str
) -> None:
    base = api_base(org, project, repo)
    import requests

    response = requests.post(
        f"{base}/pullrequests/{pr}/threads",
        headers=ado_headers(credential),
        params={"api-version": API_VERSION},
        json={"comments": [{"parentCommentId": 0, "content": text, "commentType": 1}], "status": 1},
        timeout=60,
    )
    response.raise_for_status()


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        diff = load_diff_for_args(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    prompt = build_review_prompt(diff)
    if args.dry_run:
        print("# Dry run: prompt that would be sent to Copilot")
        print(prompt)
        return 0
    if not os.environ.get("GITHUB_TOKEN"):
        print("Missing GITHUB_TOKEN (needs Copilot access)", file=sys.stderr)
        return 2
    result = asyncio.run(review(diff, args.model))
    if not result:
        print("Copilot returned no review text.", file=sys.stderr)
        return 1
    body = (
        f"## Copilot SDK code review\n\n{result}\n\n"
        "_Automated review - a human still owns the merge._"
    )
    credential = credential_from_env()
    if credential is None or args.pr is None:
        print("Missing Azure DevOps credential or PR id", file=sys.stderr)
        return 2
    post_pr_comment(args.org, args.project, args.repo, args.pr, credential, body)
    print(f"Posted review to PR {args.pr}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



