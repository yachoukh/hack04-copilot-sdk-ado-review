# Challenges

Use GitHub Copilot, Copilot Chat, inline completion, `/explain`, `/tests`, `/fix`, `@workspace`, and agent mode to complete the starter repo.

## 1. Make the starter run (20 pts)

**Goal:** Understand the repo, run the offline dry-run, and configure the Azure DevOps pipeline as a build validation policy.

**Suggested Copilot prompts:**

- Chat: `@workspace Explain the flow from Azure DevOps PR to Copilot SDK review comment.`
- Chat: `/explain review_agent.py`
- Agent mode: `Inspect the starter and list the deliberate gaps without changing files.`

**Success criteria:**

- `python review_agent.py --dry-run` prints the prompt and bundled sample diff with no credentials.
- The `Offline` pipeline stage is green on a branch.
- A PR validation run reaches the `Review` stage when `GITHUB_TOKEN` is configured.

**Hints:** Start with `parse_args`, `load_diff_for_args`, and `main`. Dry-run deliberately does not contact Copilot or Azure DevOps.

## 2. Fetch real diffs, not whole files (25 pts)

**Goal:** Replace the naive changed-file content fetch with a real PR iteration diff.

**Suggested Copilot prompts:**

- Chat: `Use the Azure DevOps PR iterations and iteration changes APIs to build a per-file unified diff.`
- Chat: `Add tests that skip lockfiles, generated code, minified files, and binary files.`
- Inline: `# build a unified diff from target and source item contents`

**Success criteria:**

- The prompt contains changed hunks rather than full file bodies.
- Large PRs are chunked per file with a character budget.
- Lockfiles, minified files, generated code, and binary files are skipped with an explicit note.

**Hints:** Use `pullRequests/{id}/iterations`, then the latest `iterations/{n}/changes`. Fetch old and new blob content only for changed files, then use Python's `difflib.unified_diff`.

## 3. Add safe tools and deny-by-default permissions (25 pts)

**Goal:** Give the agent useful context while proving that the application owns tool boundaries.

**Suggested Copilot prompts:**

- Chat: `Create a @define_tool local tool named lookup_repo_standard that reads AGENTS.md and docs.`
- Chat: `Replace PermissionHandler.approve_all with a custom deny-by-default handler that allows only an explicit allowlist.`
- Chat: `Wire Azure DevOps MCP and Microsoft Learn MCP behind an --enable-mcp flag.`

**Success criteria:**

- The reviewer can cite repo standards from `AGENTS.md`.
- Every denied permission request is logged.
- MCP is optional and the app degrades cleanly if network or `npx` is unavailable.

**Hints:** `PermissionHandler.approve_all` is intentionally unsafe in the starter. Treat it as the lesson, not as a production default.

## 4. Add a production gate and idempotent comments (20 pts)

**Goal:** Make repeated pipeline runs predictable and enforceable.

**Suggested Copilot prompts:**

- Chat: `Make the model emit a fenced JSON findings block and parse it for a severity gate.`
- Chat: `Search existing Azure DevOps PR threads for an HTML marker and update that thread instead of creating a duplicate.`
- Chat: `Fail only on Critical findings by default, with an option to also fail on High.`

**Success criteria:**

- The build fails on Critical findings.
- `--fail-on-high` also fails on High findings.
- Running the agent twice updates one bot thread rather than stacking comments.

**Hints:** Do not regex prose. Ask for a fenced `json` block, parse it, and keep human Markdown separate from the gate data.

## 5. Wildcards and evaluation (10 pts)

**Goal:** Improve trust, speed, or demo quality beyond the core reviewer.

**Suggested Copilot prompts:**

- Chat: `Create an evaluation fixture set with expected findings and precision/recall reporting.`
- Chat: `Add inline Azure DevOps comments with threadContext for changed lines.`
- Chat: `Collect review latency and estimated prompt size per run.`

**Success criteria:**

- The extra feature is demoable in five minutes.
- It makes review quality, safety, or operability measurably better.

**Hints:** Keep scope small. A clear metric beats a large half-working feature.

## Deliberate starter gaps

The starter is honest but incomplete. It leaves these lesson areas for participants:

- **Permissions:** the starter uses `PermissionHandler.approve_all`.
- **Severity gate:** the starter posts review text but does not fail on findings.
- **Chunking:** the starter fetches changed file contents and truncates, rather than building bounded per-file diffs.
- **Idempotency:** the starter creates a new PR thread on each live run.
