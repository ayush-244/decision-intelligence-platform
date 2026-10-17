"""Domain layer — the enterprise-wide business model.

The innermost layer. Pure Python with **no** dependency on FastAPI,
SQLAlchemy, Redis, or any framework. It defines:

* ``entities`` — core objects and value objects expressing business concepts.
* ``repositories`` — *interfaces* (abstract ports) that outer layers implement.

Because nothing here imports outward, the domain is trivially unit-testable and
insulated from infrastructure churn. In this foundation phase it contains only
the system-health model, which serves as the reference template for the
business domains added in later phases.
"""
