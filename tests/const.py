"""Shared seed data for the template_aliases test suite.

IDs for areas/floors are slugs generated from the name by the registry. The
`seeded` fixture asserts each generated id equals the literal here, so a change
in HA's slug rules fails loudly instead of silently skewing tests.
"""

from __future__ import annotations

ENTITY_MULTI = "switch.office_shelly"
ENTITY_MULTI_ALIASES = {"Office Light Switch", "Hallway"}
ENTITY_MULTI_SORTED = ["Hallway", "Office Light Switch"]

ENTITY_SINGLE = "light.desk"
ENTITY_SINGLE_ALIASES = {"Desk Lamp"}
ENTITY_SINGLE_SORTED = ["Desk Lamp"]

ENTITY_NO_ALIAS = "sensor.plain"

AREA_WITH = "bedroom"  # name "Bedroom"
AREA_WITH_ALIASES = {"Sleeping Room"}
AREA_WITH_SORTED = ["Sleeping Room"]

AREA_NO = "kitchen"  # name "Kitchen", no aliases

FLOOR_WITH = "basement"  # name "Basement"
FLOOR_WITH_ALIASES = {"Untergeschoss", "Keller", "Unten"}
FLOOR_WITH_SORTED = ["Keller", "Unten", "Untergeschoss"]

FLOOR_NO = "attic"  # name "Attic", no aliases

# Same slug exists as BOTH an area and a floor -> deterministic tiebreak test.
COLLISION = "garage"  # name "Garage" in both registries
COLLISION_AREA_ALIASES = {"Workshop"}
COLLISION_AREA_SORTED = ["Workshop"]
COLLISION_FLOOR_ALIASES = {"Outbuilding", "Annex", "Outhouse"}
COLLISION_FLOOR_SORTED = ["Annex", "Outbuilding", "Outhouse"]
