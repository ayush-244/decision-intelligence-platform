"""Application layer — orchestration of domain logic into use-cases.

This layer expresses *what the system does* (its use-cases/interactors) without
knowing *how* it is delivered (HTTP) or *how* data is stored (SQL/Redis). It
depends only on the domain and on abstractions (ports). It contains:

* ``use_cases`` — single-purpose interactors coordinating one operation.
* ``services`` — reusable application services shared across use-cases.
* ``dto`` — transport-agnostic data-transfer objects crossing this boundary.
"""
