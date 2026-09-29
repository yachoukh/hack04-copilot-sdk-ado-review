# Judging rubric

| Criterion | Weight | What good looks like |
|---|---:|---|
| Works end-to-end on a live PR | 30% | Pipeline validates a PR, runs the reviewer, and posts a useful Azure DevOps thread without leaking secrets. |
| Review quality | 25% | Finds the planted Critical/High issues, avoids nitpicks, gives concrete fixes, and stays within the supplied diff. |
| SDK primitives | 20% | Uses Copilot SDK sessions correctly, adds a local tool or MCP where useful, and handles permission requests explicitly. |
| Security and operability | 15% | Uses Bearer for `System.AccessToken`, PAT Basic only for PATs, denies unsafe tools, gates severe findings, and updates existing bot comments. |
| Demo and storytelling | 10% | Clearly explains what the application enforced versus what the model inferred. |

Suggested scoring bands:

- **Excellent:** Production-shaped guardrails, tests, idempotency, and a crisp demo.
- **Good:** Live review works and finds real defects with limited noise.
- **Partial:** Offline and pipeline setup work, but review output or Azure DevOps integration needs help.
- **Needs attention:** Requires manual secrets in code, uncontrolled permissions, or cannot run without facilitator rescue.
