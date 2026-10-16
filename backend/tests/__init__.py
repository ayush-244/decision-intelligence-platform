"""Test suite for the Delphi backend.

Organised into ``unit`` (fast, isolated, no I/O) and ``integration`` (exercise
the ASGI app through its public HTTP surface). External dependencies are
replaced with in-process fakes so the suite runs without PostgreSQL or Redis.
"""
