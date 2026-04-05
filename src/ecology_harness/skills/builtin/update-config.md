---
name: update-config
description: Inspect and safely adjust runtime configuration using the claw-style ConfigTool.
slug: update-config
triggers: [/update-config]
allowed-tools: [ConfigTool]
context: inline
---
Use `ConfigTool` to inspect or update the runtime configuration requested by the user.

Supported keys:
- provider
- model
- permission_mode
- sandbox_mode
- runtime_mode

If the request is ambiguous, list the current config first and then make the smallest safe change.

Requested config change:
$ARGUMENTS
