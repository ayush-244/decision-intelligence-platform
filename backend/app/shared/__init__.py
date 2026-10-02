"""Shared kernel: primitives usable by any layer without creating coupling.

Contains the application exception hierarchy and small, dependency-free
utilities. Nothing here may import from ``presentation``, ``application``,
``infrastructure`` — keeping it a safe, universally importable foundation.
"""
