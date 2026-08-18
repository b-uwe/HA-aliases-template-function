from homeassistant.helpers.template import (
    TemplateEnvironment, _ENVIRONMENT, _ENVIRONMENT_LIMITED, _ENVIRONMENT_STRICT,
)
from .aliases import AliasExtension

DOMAIN = "template_aliases"
_PATCHED = False

def _install(hass):
    global _PATCHED
    
    for key in (_ENVIRONMENT, _ENVIRONMENT_LIMITED, _ENVIRONMENT_STRICT):
        if (env := hass.data.get(key)) is not None and "aliases" not in env.globals:
            env.add_extension(AliasExtension)
    
    if not _PATCHED:
        _orig = TemplateEnvironment.__init__
        def _init(self, *a, **k):
            _orig(self, *a, **k)
            if self.hass is not None:
                self.add_extension(AliasExtension)
        TemplateEnvironment.__init__ = _init
        _PATCHED = True

async def async_setup(hass, config):
    _install(hass)
    return True

async def async_setup_entry(hass, entry):
    _install(hass)
    return True

async def async_unload_entry(hass, entry):
    return True