"""Delphi backend application package.

The package is organised as a Clean Architecture modular monolith. Dependencies
point strictly inward:

    presentation -> application -> domain
    infrastructure implements domain interfaces
    core / shared are cross-cutting and framework-agnostic

See ``docs/architecture.md`` for the full rationale.
"""

__version__ = "0.1.0"
