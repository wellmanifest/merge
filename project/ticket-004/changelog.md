# Ticket Changelog (ticket-004)

## [0.1.0] - 2026-08-14

- Initial governance scaffold created.
- No human participant identity or content was generated.
- Added `wellmanifest.operations/v1` as the canonical Commands/Queries and
  projection registry with closed JSON Schema and resolved model pointers.
- Added `wellmanifest.events/v1`: five documented, append-only,
  authority-free events whose replay is deterministic and effect-free.
- Added `wellmanifest.errors/v1`: three stable public rejection codes with
  transport status mappings and `error/[code].md` runbooks.
- Added dependency-free CQRS cross-reference conformance with nine adversarial
  cases and wired it into the existing standard entrypoint.
- Replaced four pre-existing assigned lambdas in the touched entrypoint with
  named functions so Ruff passes without changing semantics.
- Closed PR #6 without merge after discovering ticket-003 already occupied the
  integration workstream; preserved the exact implementation branch and moved
  ticket-004 to `BLOCKED / BLOCKED` pending the schedule-only canary.
