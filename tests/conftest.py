"""Shared fixtures for the template_aliases test suite.

Seeding uses the real registry helpers (entity/area/floor) rather than mocks,
so the dispatch and tiebreak behaviour is exercised against genuine registry
objects — exactly what the live instance does.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    entity_registry as er,
    floor_registry as fr,
)
from homeassistant.helpers.template import TemplateEnvironment

import custom_components.template_aliases as ta_module
from custom_components.template_aliases import DOMAIN
from custom_components.template_aliases.aliases import AliasExtension

from .const import (
    AREA_NO,
    AREA_WITH,
    AREA_WITH_ALIASES,
    COLLISION,
    COLLISION_AREA_ALIASES,
    COLLISION_FLOOR_ALIASES,
    ENTITY_MULTI,
    ENTITY_MULTI_ALIASES,
    ENTITY_NO_ALIAS,
    ENTITY_SINGLE,
    ENTITY_SINGLE_ALIASES,
    FLOOR_NO,
    FLOOR_WITH,
    FLOOR_WITH_ALIASES,
)

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load the repo's custom_components/ for every test (required by phacc)."""
    yield


@pytest.fixture(autouse=True)
def isolate_template_monkeypatch() -> Iterator[None]:
    """Undo the integration's global TemplateEnvironment.__init__ patch per test.

    __init__.py replaces ``TemplateEnvironment.__init__`` in place and flips the
    module-global ``_PATCHED``, and never restores either. Without this fixture
    the patch leaks across tests: a fresh ``TemplateEnvironment`` would auto-gain
    the extension, so the registration and per-path setup tests would pass on a
    leftover patch regardless of the code under test (order-dependent). Resetting
    to the pristine state before each test makes every such test independent.
    """
    original_init = TemplateEnvironment.__init__
    original_patched = ta_module._PATCHED
    ta_module._PATCHED = False
    try:
        yield
    finally:
        TemplateEnvironment.__init__ = original_init
        ta_module._PATCHED = original_patched


@pytest.fixture
def seeded(hass: HomeAssistant) -> None:
    """Populate entity, area and floor registries with the fixtures above."""
    ent_reg = er.async_get(hass)
    # Entity aliases are only settable through the registry's update method
    # (async_get_or_create takes no aliases argument).
    set_aliases = ent_reg.async_update_entity

    e_multi = ent_reg.async_get_or_create(
        "switch", "template_aliases", "office_shelly_uid",
        suggested_object_id="office_shelly",
    )
    assert e_multi.entity_id == ENTITY_MULTI
    set_aliases(e_multi.entity_id, aliases=ENTITY_MULTI_ALIASES)

    e_single = ent_reg.async_get_or_create(
        "light", "template_aliases", "desk_uid", suggested_object_id="desk",
    )
    assert e_single.entity_id == ENTITY_SINGLE
    set_aliases(e_single.entity_id, aliases=ENTITY_SINGLE_ALIASES)

    e_none = ent_reg.async_get_or_create(
        "sensor", "template_aliases", "plain_uid", suggested_object_id="plain",
    )
    assert e_none.entity_id == ENTITY_NO_ALIAS

    area_reg = ar.async_get(hass)
    a_with = area_reg.async_create("Bedroom", aliases=set(AREA_WITH_ALIASES))
    assert a_with.id == AREA_WITH
    a_no = area_reg.async_create("Kitchen")
    assert a_no.id == AREA_NO
    a_coll = area_reg.async_create("Garage", aliases=set(COLLISION_AREA_ALIASES))
    assert a_coll.id == COLLISION

    floor_reg = fr.async_get(hass)
    f_with = floor_reg.async_create("Basement", aliases=set(FLOOR_WITH_ALIASES))
    assert f_with.floor_id == FLOOR_WITH
    f_no = floor_reg.async_create("Attic")
    assert f_no.floor_id == FLOOR_NO
    f_coll = floor_reg.async_create("Garage", aliases=set(COLLISION_FLOOR_ALIASES))
    assert f_coll.floor_id == COLLISION

    # Lock in the collision: identical id in two registries, area reachable
    # by default, floor only via alias_type="floor".
    assert a_coll.id == f_coll.floor_id == COLLISION


@pytest.fixture
def ext(hass: HomeAssistant) -> AliasExtension:
    """An AliasExtension bound to a hass-backed template environment.

    Lets tests call the aliases() method directly (unit level) without rendering
    a full template, while still reading the real registries via self.hass.
    """
    return AliasExtension(TemplateEnvironment(hass))


@pytest.fixture
async def setup_integration(hass: HomeAssistant) -> MockConfigEntry:
    """Set up the integration through a config entry (drives the monkeypatch)."""
    entry = MockConfigEntry(domain=DOMAIN, data={}, title="Template aliases()")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry
