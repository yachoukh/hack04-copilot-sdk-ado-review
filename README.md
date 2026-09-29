# Hack 04: Copilot SDK Azure DevOps PR Review

**Format:** 1 day (or 2 x half-day) · teams of 2-4 · Python  
**Theme:** Use the **GitHub Copilot SDK** to build a PR review agent that runs in Azure DevOps and comments on pull requests.

Many customers keep their code in Azure Repos and therefore miss the native GitHub Copilot code review experience. This hackathon closes that gap: teams build the reviewer themselves with the Copilot SDK, so they learn where the model ends and where their application's guardrails begin.

## Why this scenario works for a hackathon

- **Real pain, real customers** - Azure DevOps shops with no native Copilot PR review.
- **Small surface** - one Python app, one YAML pipeline, and a planted-bug playground.
- **Deep enough** - prompt design, diff hygiene, tool and permission boundaries, MCP, idempotency, and token safety.
- **Demoable** - open a PR with deliberate bugs, watch the reviewer comment, then improve the agent live.

## Hackathon settings

- Azure DevOps org: <https://dev.azure.com/azultechlab>
- Project: `Copilot-Hackathon`
- Repo: `hack04-copilot-sdk-ado-review`
- Preferred model: `claude-sonnet-4.5` or `auto`

## Prerequisites (send to participants a week ahead)

| Need | Notes |
|---|---|
| GitHub Copilot subscription | Individual, Business or Enterprise. |
| `GITHUB_TOKEN` | PAT with Copilot access, stored as a **secret** pipeline variable. |
| Azure DevOps project + Git repo | Use org `azultechlab`, project `Copilot-Hackathon`, repo `hack04-copilot-sdk-ado-review`. |
| Build Service permission | Grant "Contribute to pull requests" on the repo so the pipeline can comment. |
| Python 3.11+ | Required by `github-copilot-sdk==1.0.14`. |
| Node 22+ | Required by the Copilot CLI runtime used by the SDK. |
| Network for runtime staging | `python -m copilot download-runtime` downloads the CLI runtime the first time. It is cached afterwards. |

Install locally:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m copilot download-runtime
```

Level 1 can start without any token:

```powershell
python review_agent.py --dry-run
```

Live PR review needs credentials:

```powershell
$env:GITHUB_TOKEN = "<github-pat-with-copilot-access>"
$env:AZURE_DEVOPS_PAT = "<ado-pat-for-local-runs>"
python review_agent.py --org azultechlab --project Copilot-Hackathon --repo hack04-copilot-sdk-ado-review --pr 42
```

In Azure Pipelines, use `System.AccessToken` instead of a PAT. The app sends `System.AccessToken` as `Authorization: Bearer <token>` because it is an OAuth token. Local `AZURE_DEVOPS_PAT` uses Basic auth with an empty username (`:<pat>`), which is the Azure DevOps PAT convention.

## Starter kit (in this folder)

| File | What it is |
|---|---|
| `review_agent.py` | Starter Python app: fetch PR changes -> Copilot SDK session -> post a PR thread. |
| `azure-pipelines.yml` | Two-stage pipeline: offline checks everywhere, live review only during PR validation when `GITHUB_TOKEN` is set. |
| `AGENTS.md` | Review standards read by the Copilot CLI runtime from the session working directory. |
| `.vscode/mcp.json` | MCP server configuration for participants using Copilot in VS Code. |
| `.github/skills/ado-pr-api/SKILL.md` | Reusable Azure DevOps PR REST API notes. |
| `samples/sample_diff.patch` | Offline dry-run diff with planted bugs. |
| `playground/` | Demo target files for creating a PR with defects. |
| `tests/` | Pytest suite with Copilot SDK mocked; no network or token needed. |

The repo contains two MCP config surfaces on purpose:

- `.vscode/mcp.json` is for Copilot in VS Code.
- `mcp_servers={...}` in the Python app is for SDK-created sessions.

They do not automatically share settings.

## Challenge ladder

Teams pick how far they climb. Points shown are a suggestion.

### Level 1 - Make it run (20 pts)

Run the offline smoke test, understand the starter flow, configure the Azure DevOps build validation policy, and get the reviewer posting a single PR thread.

### Level 2 - Make it good (25 pts)

Replace the naive changed-file content fetch with real iteration diffs, chunk large PRs per file, skip lockfiles/generated/minified/binary files, and tune the prompt to reduce noise while keeping Critical and High findings.

### Level 3 - Give it tools and boundaries (25 pts)

Add local tools or MCP, but keep permissions deny-by-default. Use `AGENTS.md` as the review standard and make tool access explicit and auditable.

### Level 4 - Make it production-shaped (20 pts)

Add a severity gate, idempotent PR thread updates, inline comments with `threadContext`, and cleaner failure modes.

### Level 5 - Wildcards (10 pts)

Build an evaluation harness, cost/latency dashboard, richer work-item grounding through Azure DevOps MCP, or a repo-standard citation requirement.

## Judging rubric

| Criterion | Weight |
|---|---:|
| Works end-to-end on a live PR | 30% |
| Review quality: real findings, low noise | 25% |
| Use of SDK primitives: sessions, tools, permissions, MCP | 20% |
| Security and operability: secrets, idempotency, failure modes | 15% |
| Demo and storytelling | 10% |

See `RUBRIC.md` for the standalone scoring guide.

## Suggested agenda (one day)

| Time | Item |
|---|---|
| 09:00 | Kickoff: agentic code review, SDK vs CLI vs native Copilot review. |
| 09:30 | Preflight: everyone runs `python review_agent.py --dry-run`. |
| 10:00 | Level 1: pipeline and live PR comment. |
| 11:30 | Level 2: real diffs, chunking, review quality. |
| 13:30 | Level 3: tools, AGENTS.md, MCP, permissions. |
| 15:30 | Level 4 and wildcards: gate, idempotency, inline comments, evaluation. |
| 16:30 | Demos, 5 minutes per team. |
| 17:15 | Judging and wrap: what did the app prove, and what did the model assert? |

## Planted-bug playground

Create a feature branch that changes files under `playground/`, then open a PR into `main`. The starter dry-run uses `samples/sample_diff.patch`; the live demo can use the same defects in real files.

A good reviewer finds the security and correctness defects with severities and concrete fixes. A noisy reviewer also complains about naming or docstrings. That is the Level 2 tuning problem.

## Reference material

- GitHub Copilot SDK - <https://github.com/github/copilot-sdk>
- Copilot SDK docs - <https://docs.github.com/en/copilot/how-tos/copilot-sdk>
- Official Copilot SDK workshops - <https://github.com/github/copilot-sdk-workshop>
- Azure DevOps PR threads REST API - <https://learn.microsoft.com/en-us/rest/api/azure/devops/git/pull-request-threads>
- Azure DevOps native Copilot code review preview - <https://learn.microsoft.com/en-us/azure/devops/repos/git/copilot-code-reviews>
- Azure DevOps MCP server - <https://mcp.dev.azure.com/azultechlab>
- Microsoft Learn MCP server - <https://learn.microsoft.com/api/mcp>

## Facilitator notes

- The Copilot SDK is in technical preview. Pin `github-copilot-sdk==1.0.14` and keep the runtime cache warm.
- Budget 10-15 minutes for the first `python -m copilot download-runtime` on constrained networks.
- `AGENTS.md` is not decorative: the Copilot CLI runtime reads it from the session working directory and uses it as repository guidance.
- Push teams to show one application-owned guardrail in their demo: diff boundaries, permission denial, severity gate, or idempotency.
- Do not run Azure deployments for this hack. The only Azure DevOps mutation is a PR comment thread.
