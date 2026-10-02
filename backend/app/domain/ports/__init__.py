"""Domain ports (outbound interfaces).

Ports describe capabilities the domain needs from the outside world without
knowing their implementation. Persistence repository interfaces will live in
``domain/repositories/``; non-persistence ports (health probes, messaging,
object storage) belong here.
"""

from app.domain.ports.health_probe import HealthProbe

__all__ = ["HealthProbe"]
