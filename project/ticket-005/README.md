# Ticket 005: Complete the command rejection surface

- **ID**: ticket-005
- **Owner**: unresolved:human
- **Status**: DONE
- **Workflow state**: DONE
- **Created**: 2026-08-14

## Goal and scope

`error/index.json` closes exactly over the codes the commands declare in
`rejects`, which is the right invariant — but those lists named three codes
while the validators raise nine. A request could be refused with
`MRG-RECOVERY-001` or `MRG-SECRET-001`, and the catalogue said the command had
no such refusal and offered no document to read.

Complete the surface from the validators themselves, register and document the
codes that were missing, and add the rule that keeps the two in step: each
command's declared rejections must equal the diagnostics its own validator can
raise, derived with `ast` rather than kept by hand.

Authoring diagnostics stay out of it. `CQRS-*` and `MRG-CONTRACT-001` refuse a
malformed standard, not a request, so they are not command rejections.

## Acceptance criteria

- [x] AC-01: The CQRS suite passes with the completed lists, and the error
  catalogue still closes over the command rejections exactly.
- [x] AC-02: The decision suite passes and reports the derived surface: 4, 4, 7
  and 5 codes for the four commands.
- [x] AC-03: Dropping a declared code from the registry is rejected with
  `MRG-CQRS-001` instead of passing silently.

## Participants

- Human participant: unresolved; no user-* file was created by this script.
- Agent participant: [ai-claude.md](ai-claude.md)
