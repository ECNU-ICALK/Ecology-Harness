---
name: verify
description: Run the smallest high-signal verification steps before concluding work.
slug: verify
triggers: [/verify]
allowed-tools: [GetDiagnostics, Bash, Read, Glob, Grep]
context: inline
---
Verify the requested change with the lightest checks that still build confidence.

Preferred order:
1. read the touched files if needed
2. run narrow diagnostics or targeted tests
3. summarize what passed, what was not run, and any residual risk

If the user gave a specific verification target, optimize for that:
$ARGUMENTS
