"""LeakGuard: a semantic DLP guardrail for LiteLLM Proxy.

Layers (from LeakGuard_class_diagram_v11):
    domain          aggregates, value objects, the inspection pipeline and the ports
    application     the five services (they never hold each other)
    infrastructure  the LiteLLM hook, repository implementations, security and model adapters

Every dependency points toward the domain (dependency inversion).
"""
