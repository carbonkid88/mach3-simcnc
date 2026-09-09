# Safety Notice

This project works with CNC controller configuration data. Incorrect migration
results can cause unexpected machine motion, damaged tools, damaged machines,
or injury.

## Current Safety Status

MACH3 -> simCNC is an early community validation tool. It reads and displays
profile data to support migration work. It does not provide a validated,
machine-ready simCNC configuration.

No displayed, interpreted, generated, or copied value should be trusted without
manual verification by a qualified person.

## Always Verify

Before using any migrated value:

- verify units and scaling
- verify axis directions and motor mappings
- verify homing direction, homing speed, and reference behavior
- verify soft limits and hard limits
- verify input and output signal names
- verify port/pin or hardware terminal mappings
- verify spindle control and speed scaling
- verify safety circuits and emergency stop behavior

## Recommended Test Order

1. Inspect values offline.
2. Compare with the original MACH3 profile and a known-good simCNC reference.
3. Test in simCNC without enabling real machine motion where possible.
4. Test with drives disabled or disconnected where practical.
5. Test one axis or signal at a time.
6. Test without a tool, workpiece, or unsafe spindle operation.
7. Keep emergency stop available and verified.

## Sharing Profiles

Profiles can contain sensitive information, including local file paths,
customer names, macros, machine names, comments, or site-specific setup data.
Anonymize files before attaching them to issues or pull requests.

When in doubt, share only the smallest XML snippet needed to reproduce a parser
or mapping issue.
