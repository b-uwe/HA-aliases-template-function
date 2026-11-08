"""Behavioural tests for the aliases() template function/filter.

Layers:
* direct calls to AliasExtension.aliases(...) for dispatch/unhappy/error logic,
* direct environment inspection for global+filter registration,
* setup-driven tests that exercise the TemplateEnvironment.__init__ monkeypatch
  and render real templates end to end.
"""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.template import _ENVIRONMENT, Template, TemplateEnvironment
from homeassistant.setup import async_setup_component

from custom_components.template_aliases import DOMAIN
from custom_components.template_aliases.aliases import AliasExtension

from .const import (
    AREA_NO,
    AREA_WITH,
    AREA_WITH_SORTED,
    COLLISION,
    COLLISION_AREA_SORTED,
    COLLISION_FLOOR_SORTED,
    ENTITY_MULTI,
    ENTITY_MULTI_SORTED,
    ENTITY_NO_ALIAS,
    ENTITY_SINGLE,
    ENTITY_SINGLE_SORTED,
    FLOOR_NO,
    FLOOR_WITH,
    FLOOR_WITH_SORTED,
)

# (lookup_value, alias_type, expected) — alias_type=None means "auto dispatch".
RETURN_CASES = [
    # --- happy: entities ---
    (ENTITY_MULTI, None, ENTITY_MULTI_SORTED),
    (ENTITY_MULTI, "entity", ENTITY_MULTI_SORTED),
    (ENTITY_SINGLE, None, ENTITY_SINGLE_SORTED),
    # cv.entity_id normalises case; entity lookup is case-insensitive.
    (ENTITY_MULTI.upper(), None, ENTITY_MULTI_SORTED),
    (ENTITY_MULTI.upper(), "entity", ENTITY_MULTI_SORTED),
    # --- happy: areas ---
    (AREA_WITH, None, AREA_WITH_SORTED),
    (AREA_WITH, "area", AREA_WITH_SORTED),
    # --- happy: floors (auto falls through entity -> area -> floor) ---
    (FLOOR_WITH, None, FLOOR_WITH_SORTED),
    (FLOOR_WITH, "floor", FLOOR_WITH_SORTED),
    # --- no aliases -> [] ---
    (AREA_NO, None, []),
    (FLOOR_NO, None, []),
    (FLOOR_NO, "floor", []),
    (ENTITY_NO_ALIAS, None, []),
    (ENTITY_NO_ALIAS, "entity", []),
    # --- collision: same slug is both an area and a floor ---
    (COLLISION, None, COLLISION_AREA_SORTED),      # area wins by default
    (COLLISION, "area", COLLISION_AREA_SORTED),
    (COLLISION, "floor", COLLISION_FLOOR_SORTED),  # floor only via alias_type
    # --- forcing the wrong registry -> [] ---
    (ENTITY_MULTI, "floor", []),
    (ENTITY_MULTI, "area", []),
    (AREA_WITH, "floor", []),
    (FLOOR_WITH, "area", []),
    # --- unhappy inputs (all -> [], never raise) ---
    ("switch.nonexistent", None, []),
    ("switch.nonexistent", "entity", []),
    ("", None, []),
    ("   ", None, []),
    (123, None, []),
    (None, None, []),
    ("unknown_bare_slug", None, []),
]

RETURN_IDS = [
    "entity-multi-auto",
    "entity-multi-explicit",
    "entity-single-auto",
    "entity-uppercase-auto",
    "entity-uppercase-explicit",
    "area-auto",
    "area-explicit",
    "floor-auto-fallthrough",
    "floor-explicit",
    "area-no-aliases",
    "floor-no-aliases-auto",
    "floor-no-aliases-explicit",
    "entity-no-aliases-auto",
    "entity-no-aliases-explicit",
    "collision-auto-area-wins",
    "collision-explicit-area",
    "collision-explicit-floor",
    "entity-forced-floor",
    "entity-forced-area",
    "area-forced-floor",
    "floor-forced-area",
    "unknown-entity-id-auto",
    "unknown-entity-id-explicit",
    "empty-string",
    "whitespace",
    "int-123",
    "none",
    "unknown-bare-slug",
]


@pytest.mark.parametrize(("lookup", "alias_type", "expected"), RETURN_CASES, ids=RETURN_IDS)
def test_aliases_return_values(
    ext: AliasExtension, seeded: None, lookup, alias_type, expected
) -> None:
    """Dispatch, tiebreak and unhappy-path results match the live instance."""
    assert ext.aliases(lookup, alias_type) == expected


def test_result_is_sorted_list_not_string(ext: AliasExtension, seeded: None) -> None:
    """Return type is a list[str] in sorted order, never a bare string."""
    result = ext.aliases(ENTITY_MULTI)
    assert isinstance(result, list)
    assert not isinstance(result, str)
    assert result == sorted(result)


@pytest.mark.parametrize("bad_type", ["banana", "Area", ""], ids=["banana", "Area-case", "empty"])
def test_invalid_alias_type_raises_valueerror(ext: AliasExtension, bad_type) -> None:
    """Invalid alias_type raises ValueError listing the valid values."""
    with pytest.raises(ValueError) as err:
        ext.aliases(ENTITY_MULTI, bad_type)
    message = str(err.value)
    assert "'entity'" in message
    assert "'area'" in message
    assert "'floor'" in message


def test_global_and_filter_both_registered(hass: HomeAssistant) -> None:
    """The function registers as BOTH a global and a filter named 'aliases'."""
    env = TemplateEnvironment(hass)
    AliasExtension(env)
    assert "aliases" in env.globals
    assert "aliases" in env.filters


async def test_setup_entry_exposes_aliases_in_fresh_env(
    hass: HomeAssistant, setup_integration
) -> None:
    """After config-entry setup, a freshly built environment carries aliases.

    This drives the TemplateEnvironment.__init__ monkeypatch — the riskiest part.
    """
    env = TemplateEnvironment(hass)
    assert "aliases" in env.globals
    assert "aliases" in env.filters


async def test_async_setup_yaml_exposes_aliases_in_fresh_env(hass: HomeAssistant) -> None:
    """The YAML setup path (async_setup) also installs the monkeypatch."""
    assert await async_setup_component(hass, DOMAIN, {})
    env = TemplateEnvironment(hass)
    assert "aliases" in env.globals
    assert "aliases" in env.filters


async def test_render_global_syntax(
    hass: HomeAssistant, setup_integration, seeded: None
) -> None:
    """Global syntax aliases('switch.office_shelly') renders the sorted list."""
    result = Template("{{ aliases('switch.office_shelly') }}", hass).async_render()
    assert result == ENTITY_MULTI_SORTED


async def test_render_filter_syntax_no_arg(
    hass: HomeAssistant, setup_integration, seeded: None
) -> None:
    """Filter syntax x | aliases auto-dispatches; area wins the collision."""
    result = Template("{{ 'garage' | aliases }}", hass).async_render()
    assert result == COLLISION_AREA_SORTED


async def test_render_filter_syntax_with_arg(
    hass: HomeAssistant, setup_integration, seeded: None
) -> None:
    """Filter syntax x | aliases('floor') reaches the colliding floor."""
    result = Template("{{ 'garage' | aliases('floor') }}", hass).async_render()
    assert result == COLLISION_FLOOR_SORTED


async def test_render_non_str_lookup_returns_empty(
    hass: HomeAssistant, setup_integration, seeded: None
) -> None:
    """A non-str value in the render path is coerced and yields [] (no crash)."""
    result = Template("{{ 123 | aliases }}", hass).async_render()
    assert result == []


async def test_setup_patches_already_cached_environments(hass: HomeAssistant) -> None:
    """_install also upgrades environments already cached in hass.data.

    On a live instance the cached _ENVIRONMENT* objects are what already exists;
    this exercises the cached-env loop, not only the monkeypatch for new envs.
    """
    cached = TemplateEnvironment(hass)  # built pre-patch -> no extension yet
    assert "aliases" not in cached.globals
    hass.data[_ENVIRONMENT] = cached

    assert await async_setup_component(hass, DOMAIN, {})

    assert "aliases" in cached.globals
    assert "aliases" in cached.filters


def test_function_skipped_when_environment_has_no_hass() -> None:
    """requires_hass=True drops the function when the environment has no hass."""
    env = TemplateEnvironment(None)
    AliasExtension(env)
    assert "aliases" not in env.globals
    assert "aliases" not in env.filters


async def test_config_flow_user_step_creates_entry(hass: HomeAssistant) -> None:
    """The UI flow's user step creates the entry with the expected title/data."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Template aliases()"
    assert result["data"] == {}
    await hass.async_block_till_done()


async def test_config_flow_aborts_when_already_configured(hass: HomeAssistant) -> None:
    """single_config_entry: a second user flow aborts instead of creating a 2nd entry."""
    MockConfigEntry(domain=DOMAIN, data={}).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "single_instance_allowed"


async def test_unload_entry_returns_true(
    hass: HomeAssistant, setup_integration
) -> None:
    """The config entry unloads cleanly."""
    assert await hass.config_entries.async_unload(setup_integration.entry_id)
