"""F2.4 — full portable-domain cycle through the real upstream runtime.

This module does not modify upstream source files. It temporarily injects the
F2.3 resolver into the two module-level lookup functions used by the current
upstream run_governed_runtime_cycle():

    is_supported_domain(domain)
    resolve_domain_pipeline(domain)

The rest of the upstream runtime remains untouched and therefore exercises the
real context, decision-record, OS3 ticket, replay, execution gate, receipt and
feedback rails.

The injection is process-local, explicit, serialized, and always restored.
"""
from __future__ import annotations

from contextlib import contextmanager
import threading
from pathlib import Path
from typing import Any, Iterator

from universal.runtime.resolver_v0 import CanonicalCompatibleResolverV0


class PortableRuntimeInjectionError(RuntimeError):
    pass


_INJECTION_LOCK = threading.RLock()


def _load_upstream_runtime(resolver: CanonicalCompatibleResolverV0):
    # F2.3 already imports the real upstream runtime from the frozen checkout.
    runtime = getattr(resolver, "_runtime", None)
    if runtime is None:
        raise PortableRuntimeInjectionError("resolver has no upstream runtime")
    if not hasattr(runtime, "run_governed_runtime_cycle"):
        raise PortableRuntimeInjectionError(
            "upstream runtime has no run_governed_runtime_cycle"
        )
    return runtime


@contextmanager
def inject_portable_resolver_v0(
    resolver: CanonicalCompatibleResolverV0,
) -> Iterator[Any]:
    """Temporarily bind portable resolution into the real upstream coordinator.

    Only the two resolution callables are replaced. They are restored in a
    finally block even when the cycle raises.
    """

    runtime = _load_upstream_runtime(resolver)

    with _INJECTION_LOCK:
        original_supported = runtime.is_supported_domain
        original_resolve = runtime.resolve_domain_pipeline

        if getattr(runtime, "_portable_resolver_injected_v0", False):
            raise PortableRuntimeInjectionError(
                "portable resolver injection already active"
            )

        runtime._portable_resolver_injected_v0 = True
        runtime.is_supported_domain = resolver.is_supported_domain
        runtime.resolve_domain_pipeline = resolver.resolve_domain_pipeline

        try:
            yield runtime
        finally:
            runtime.is_supported_domain = original_supported
            runtime.resolve_domain_pipeline = original_resolve
            runtime._portable_resolver_injected_v0 = False


def run_portable_governed_runtime_cycle(
    resolver: CanonicalCompatibleResolverV0,
    agent_id: str,
    action: Any,
    domain_state: Any,
    **kwargs: Any,
):
    """Run the real upstream full governed cycle with portable resolution.

    This function grants no new authority. It delegates the entire lifecycle to
    the real upstream run_governed_runtime_cycle().
    """

    with inject_portable_resolver_v0(resolver) as runtime:
        return runtime.run_governed_runtime_cycle(
            agent_id,
            action,
            domain_state,
            **kwargs,
        )
