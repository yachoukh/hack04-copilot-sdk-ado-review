---
name: ado-pr-api
description: Azure DevOps pull request REST API conventions for Copilot review agents, including auth schemes, PR iterations, changed files, threads, inline threadContext, and idempotent comments.
---

# Azure DevOps PR API conventions

Use this skill when writing code that reads or comments on Azure Repos pull requests.

## Base URL

Repository-scoped APIs use:

```text
https://dev.azure.com/{org}/{project}/_apis/git/repositories/{repo}
```

Use `api-version=7.1` unless a newer version is deliberately tested. URL-encode `project`, `repo`, branch names, and paths in query parameters.

## Authentication

- Pipeline `System.AccessToken`: OAuth token. Send `Authorization: Bearer <token>`.
- Local `AZURE_DEVOPS_PAT`: PAT. Send `Authorization: Basic <base64(':<pat>')>`.

Do not send `System.AccessToken` as Basic. Basic with an empty username works for PATs, not for the pipeline OAuth token.

## Reading PR diffs

Prefer PR iterations over commit diff shortcuts:

1. `GET .../pullRequests/{pullRequestId}/iterations?api-version=7.1`
2. Choose the latest iteration id.
3. `GET .../pullRequests/{pullRequestId}/iterations/{iterationId}/changes?api-version=7.1`
4. For each changed blob, fetch old and new item content by commit id when needed.
5. Build a per-file unified diff with bounded context.

Skip folders, binaries, lockfiles, generated files, minified files, and vendored dependencies.

## Posting comments

Create a PR thread:

```http
POST .../pullRequests/{pullRequestId}/threads?api-version=7.1
```

Payload:

```json
{
  "comments": [{"parentCommentId": 0, "content": "Markdown", "commentType": 1}],
  "status": 1
}
```

For inline comments, include `threadContext`:

```json
{
  "threadContext": {
    "filePath": "/src/app.py",
    "rightFileStart": {"line": 42, "offset": 1},
    "rightFileEnd": {"line": 42, "offset": 1}
  }
}
```

Line numbers must refer to the changed right-side file in the latest iteration.

## Idempotency

Embed a stable HTML marker in bot comments, for example:

```html
<!-- copilot-sdk-ado-review:repo-wide -->
```

Before creating a thread, `GET .../pullRequests/{pullRequestId}/threads`, search active and fixed threads for that marker, and update the first matching thread comment. Re-running the pipeline should produce one bot thread, not one per push.

## Gotchas

- `System.PullRequest.PullRequestId` exists only in PR validation builds.
- `System.TeamFoundationCollectionUri` is a URL; `--org` needs the org name, such as `azultechlab`.
- Azure DevOps paths usually start with `/` in API responses.
- `item.isFolder` means skip content fetching.
- Large generated diffs can waste tokens and hide important findings; skip them before calling the model.
