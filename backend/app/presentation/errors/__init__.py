"""Centralised HTTP error handling.

Provides a single, consistent JSON error envelope and the handlers that map
every failure mode — application errors, request-validation errors, and
unexpected exceptions — onto it. Registered on the app in ``app.main`` so no
router needs bespoke error handling.
"""

from app.presentation.errors.handlers import register_exception_handlers

__all__ = ["register_exception_handlers"]
