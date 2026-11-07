# Repository instructions

Scope: this entire 2027RTC repository.

- Read README.md, CONTRIBUTING.md and the relevant directory README before edits.
- Treat docs/architecture.md and docs/interfaces.md as drafts until their status changes.
- Do not assume a specific MCU, sensor, pinout or flight configuration from examples.
- Keep the root README brief; put detailed procedures in docs/ and link through docs/README.md.
- Make focused changes. Update affected documentation and interfaces together.
- Preserve existing user work and necessary third-party source and license information.
- Use relative paths for shared assets. Keep personal configuration and credentials out of commits.
- For hardware or CAD changes, describe affected files and required visual/electrical checks.
- Report only checks performed; distinguish docs, builds, host tests, board tests and system tests.
- For documentation changes, run python tools/check_docs.py or python3 tools/check_docs.py.
- A passing documentation check does not validate hardware, firmware or flight readiness.
- GitHub permissions, branch protection, code owners and labels require actual repository configuration.
