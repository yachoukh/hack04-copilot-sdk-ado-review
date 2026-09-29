import base64
from pathlib import Path

import review_agent


def test_parse_args_dry_run_defaults():
    args = review_agent.parse_args(["--dry-run"])
    assert args.dry_run is True
    assert args.org == "azultechlab"
    assert args.project == "Copilot-Hackathon"
    assert args.repo == "hack04-copilot-sdk-ado-review"
    assert args.pr is None


def test_auth_scheme_prefers_system_access_token():
    credential = review_agent.credential_from_env(
        {"SYSTEM_ACCESSTOKEN": "oauth-token", "AZURE_DEVOPS_PAT": "pat-token"}
    )
    assert credential is not None
    assert review_agent.ado_headers(credential)["Authorization"] == "Bearer oauth-token"


def test_auth_scheme_uses_basic_for_pat():
    credential = review_agent.credential_from_env({"AZURE_DEVOPS_PAT": "pat-token"})
    assert credential is not None
    expected = base64.b64encode(b":pat-token").decode()
    assert review_agent.ado_headers(credential)["Authorization"] == f"Basic {expected}"


def test_org_from_collection_uri():
    org = review_agent.org_from_collection_uri("https://dev.azure.com/azultechlab/")
    assert org == "azultechlab"


def test_should_skip_diff_file():
    assert review_agent.should_skip_diff_file("/src/package-lock.json")
    assert review_agent.should_skip_diff_file("/dist/app.min.js")
    assert review_agent.should_skip_diff_file("/generated/client.py")
    assert not review_agent.should_skip_diff_file("/src/customer_portal.py")


def test_dry_run_prints_prompt_without_credentials(capsys, monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("SYSTEM_ACCESSTOKEN", raising=False)
    monkeypatch.delenv("AZURE_DEVOPS_PAT", raising=False)
    code = review_agent.main(["--dry-run", "--sample-diff", str(Path("samples/sample_diff.patch"))])
    out = capsys.readouterr().out
    assert code == 0
    assert "Dry run" in out
    assert "Review this pull request" in out
    assert "SQL" in out or "SELECT" in out



class _FakeData:
    def __init__(self, content):
        self.content = content


class _FakeEvent:
    """Mimics SessionEvent: payload lives in .data, and there is no .content."""

    def __init__(self, content):
        self.data = _FakeData(content)
        self.type = "assistant.message"


def test_reply_text_reads_nested_event_data():
    """SessionEvent has no .content, only .data.content."""
    assert review_agent.reply_text(_FakeEvent("  ## Findings  ")) == "## Findings"


def test_review_timeout_default_exceeds_sdk_default():
    """send_and_wait defaults to 60s and raises TimeoutError; reviews take longer."""
    assert review_agent.REVIEW_TIMEOUT_SECONDS > 60.0
    assert review_agent.parse_args([]).timeout == review_agent.REVIEW_TIMEOUT_SECONDS
