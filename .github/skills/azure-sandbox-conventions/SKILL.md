---
name: azure-sandbox-conventions
description: Naming, tagging, region and safety rules for the AzulTech Copilot hackathon Azure sandbox. Use whenever creating, renaming, tagging or deploying any Azure resource, writing Bicep, or writing Python/PowerShell that queries or filters hackathon resources, so that generated code matches the shared sandbox and never touches resources outside it.
---

# Azure sandbox conventions (Copilot hackathon)

These rules apply to every hackathon repo. Follow them before inventing your own.

## Subscription and region

- Subscription: the shared hackathon sandbox only. Never target another subscription.
- Region: **`swedencentral`** for every resource. Do not use `westeurope` or `northeurope`.
- Never create or delete resource groups outside the `rg-copilot-hack-*` prefix.

## Resource groups

| Resource group | Purpose |
|---|---|
| `rg-copilot-hack-shared` | Log Analytics workspace, VNet, private endpoint subnet, private DNS zones. **Read-only** — reference, never modify. |
| `rg-copilot-hack-deploy` | Target for participant Bicep deployments. |
| `rg-copilot-hack-tags-demo` | Seeded resources with deliberate tag violations. |
| `rg-copilot-hack-stale-01` … `-04` | Seeded resource groups with `lastReviewed` tags for stale-resource exercises. |

## Naming convention

`<type-abbrev>-<workload>-<env>-<region-abbrev>[-<suffix>]`

- `env` is `dev` for all hackathon work.
- `region-abbrev` for Sweden Central is `sdc`.
- Globally unique names (Key Vault, storage) take a short deterministic `suffix`.
- Storage accounts drop dashes and stay lowercase, max 24 characters.
- Key Vault names are max 24 characters.

Examples: `kv-hack-dev-sdc-svmu5i`, `sthackdevsdcsvmu5ipj`, `law-copilot-hack`, `vnet-copilot-hack`.

> **Key Vault soft delete:** purge protection reserves a deleted vault name for 90 days.
> Templates expose a `nameSuffix` parameter so a facilitator can bump the name after a
> teardown. `nameSuffix = ''` must always reproduce the original seeded name — changing the
> naming scheme unconditionally creates duplicate resources instead of updating them.
> **Always run `what-if` before deploying a naming change.**

## Mandatory tags

Every resource and resource group carries all six:

| Tag | Allowed values / format |
|---|---|
| `purpose` | free text, must be non-empty |
| `owner` | free text (team or person) |
| `costCenter` | `CC-` followed by 4 digits, e.g. `CC-1234` |
| `environment` | `dev`, `test` or `prod` (hackathon uses `dev`) |
| `application` | free text, must be non-empty |
| `dataClassification` | `public`, `internal`, `confidential` or `restricted` |

Rules when writing code that reads tags:

- **Azure tag keys are case-insensitive.** Compare case-insensitively or you will report false violations.
- A resource with **no tags at all** returns `None`, not `{}`. Guard for it.
- Tag values may be empty strings — treat empty as missing.

## Safety rules for generated code

- Destructive operations (`delete`, `purge`, `remove`) must be gated behind an explicit
  opt-in flag and must default to a dry run.
- Filter by the `rg-copilot-hack-*` prefix **and** a hackathon tag before deleting anything.
- Never write a credential, connection string, PAT or subscription ID into a repo file.
  Use environment variables and a committed `.env.example` with placeholder values.
- Never output a secret value from a Bicep module. Output names, IDs and URIs only.

## Known SDK and tooling pitfalls

- `azure-mgmt-resource` 26+ moved the client. The correct import is
  `from azure.mgmt.resource.resources import ResourceManagementClient`.
  The older `from azure.mgmt.resource import ResourceManagementClient` raises `ImportError`.
  Copilot frequently suggests the old one — verify it.
- PowerShell `-WhatIf` cascades to **every** `ShouldProcess` cmdlet in the call, including
  `Export-Csv` and `New-Item`, so a dry run can silently write no report. Pass
  `-WhatIf:$false` on cmdlets that must always execute.
- Resource listings are paginated. Consume the full paged iterator; do not take the first page.
