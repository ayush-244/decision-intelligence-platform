"""Cross-cutting bootstrap concerns shared by every layer.

`core` deliberately sits outside the Clean Architecture layer stack because its
contents (typed configuration, logging setup, application constants) are
framework-agnostic primitives consumed everywhere — including the composition
root in ``app.main``. Keeping them here (rather than under ``infrastructure``)
avoids inverted dependencies where the domain would otherwise need to import an
infrastructure package.
"""
