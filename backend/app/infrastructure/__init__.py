"""Infrastructure layer — concrete adapters to the outside world.

Implements the ports declared by the domain and provides technical capabilities
(database, cache) to the composition root. This is the only layer permitted to
import third-party I/O libraries such as SQLAlchemy, asyncpg, and redis. It
depends inward on the domain (to implement its interfaces) but nothing depends
on it directly — wiring happens in ``app.presentation.api.deps`` and
``app.main``.
"""
