"""Config flow so the integration can be added via the UI (no YAML needed)."""

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult

from . import DOMAIN


class TemplateAliasesConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-step flow: nothing to configure, just create the entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the entry immediately; there are no options."""
        return self.async_create_entry(title="Template aliases()", data={})
