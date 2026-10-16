# ADR-010: Unified Decision Workspace

## Status

Accepted — Phase 10

## Context

Phases 1–9 delivered discrete analytical modules (statistics, causal, simulation, decision, executive) each with separate pages. Users lost context switching between modules and had no persistent record of an analytical journey.

## Decision

Introduce a **DecisionSession** aggregate that links all phase artifacts and a **Unified Workspace** frontend that becomes the primary entry point. Search, timeline, and comparison are first-class workspace capabilities.

## Consequences

- New tables: `decision_sessions`, `session_activities`
- Existing module routes remain; workspace deep-links into them
- Audit log repository extended with `list_for_organization` for activity API
- Collaboration primitives (comments) stored as session activities without real-time sync
