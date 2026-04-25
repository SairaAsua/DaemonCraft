# Plan for DC-30

## Goal
Design how Human Design System concepts map to agent behavior in DaemonCraft.

## Research Questions
1. What HD data does each agent need? (type, strategy, authority, profile, defined centers, gates, channels, variable)
2. How does this data affect agent prompts? (SOUL injection, dynamic context)
3. How does this data affect agent decisions? (goal selection, social interaction, risk tolerance)
4. What is the storage format? (JSON per agent, shared definitions)
5. How do transits work? (daily gate activations, temporary modifiers)
6. How do variable life arcs work? (age thresholds 0-30, 30-50, 50+)

## Deliverables
- [ ] agents/docs/human-design-architecture.md
- [ ] Proposed data model (JSON schema)
- [ ] Prompt injection strategy (how SOULs incorporate HD)
- [ ] Decision modifier spec (how HD affects goal selection)
- [ ] Transit calculation approach

## Next Steps After This Spike
- DC-31: Implement profile archetypes
- DC-32: Implement type-based strategy
