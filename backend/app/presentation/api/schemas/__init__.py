"""Pydantic request/response schemas for the HTTP boundary.

Schemas are distinct from application DTOs and domain entities on purpose: the
wire contract can evolve (field names, examples, deprecation) independently of
the internal model, and OpenAPI documentation is generated from these types.
"""
