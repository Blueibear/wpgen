from __future__ import annotations
import os
import importlib
import sys

def test_provider_resolution_debug():
    # What does CI think the env is
    env = os.getenv("WPGEN_PROVIDER", "<unset>")
    print("WPGEN_PROVIDER =", env, file=sys.stderr)

    # Import factory fresh to avoid stale module state
    factory = importlib.import_module("wpgen.llm.factory")

    # Print the provider map keys for visibility
    provider_map = getattr(factory, "_PROVIDER_MAP", {})
    print("Factory providers =", sorted(list(provider_map.keys())), file=sys.stderr)

    # Resolve and instantiate
    Provider = factory.get_provider_class(env)
    inst = Provider()  # should not be abstract
    print("Resolved provider class =", Provider.__name__, file=sys.stderr)

    # If it is the mock, it should expose deterministic behavior
    if Provider.__name__.lower().startswith("mock"):
        out = inst.generate_code("test", "php")
        assert "<?php" in out
