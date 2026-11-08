"""Graceful-degradation test for the private-core-API import guard.

__init__.py imports private template internals under try/except: on ImportError
it sets ``_IMPORTS_OK = False`` and ``async_setup`` returns ``False`` instead of
taking Home Assistant down. This module REALLY simulates that failure: it forces
the private import to raise (monkeypatching ``builtins.__import__``), reloads the
integration, and asserts ``_IMPORTS_OK is False`` and that ``async_setup``
returns ``False`` — rather than merely asserting on the flag.
"""

from __future__ import annotations

import builtins
import importlib

from homeassistant.core import HomeAssistant


async def test_async_setup_returns_false_when_private_api_missing(
    hass: HomeAssistant, monkeypatch
) -> None:
    """Simulated ImportError of the private API disables setup (no crash)."""
    import custom_components.template_aliases as ta_module

    real_import = builtins.__import__

    def failing_import(name, globalns=None, localns=None, fromlist=(), level=0):
        # The integration does `from homeassistant.helpers.template import (...)`.
        if name == "homeassistant.helpers.template" and fromlist and (
            "TemplateEnvironment" in fromlist
        ):
            raise ImportError("simulated: private template API changed")
        return real_import(name, globalns, localns, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", failing_import)
    try:
        reloaded = importlib.reload(ta_module)
        assert reloaded._IMPORTS_OK is False
        assert await reloaded.async_setup(hass, {}) is False
    finally:
        # Restore the real import and a healthy module for the rest of the suite.
        monkeypatch.undo()
        importlib.reload(ta_module)
