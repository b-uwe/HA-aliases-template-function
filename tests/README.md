# Tests

Run from the **repo root** (so `custom_components/` is importable), inside a
project-local virtual environment only:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_test.txt
python -m pytest tests/ -v
```

Never install into system/global Python and never use
`--break-system-packages`, `--user`, or `sudo pip`.

The suite requires the private core template-extensions API
(`homeassistant.helpers.template.extensions.base`), which the version floor
`pytest-homeassistant-custom-component>=0.13.298` (Home Assistant 2025.12.0)
guarantees.

## What is covered

- `tests/test_aliases.py` — behaviour of the `aliases()` global/filter:
  dispatch order (entity → area → floor), the area-before-floor tiebreak on a
  colliding slug, entity-id case handling (`cv.entity_id` lowercases; area/floor
  are exact-match), every unhappy input (`[]`, no crash), `ValueError` on invalid
  `alias_type`, both-registrations check, the `requires_hass` skip, the config
  flow, entry unload, and setup-driven (config entry + YAML) rendering through
  the `TemplateEnvironment.__init__` monkeypatch (incl. already-cached envs).
- `tests/test_degradation.py` — simulated private-API `ImportError` disables
  setup (`async_setup` returns `False`).
- `tests/conftest.py` — seeds the real entity/area/floor registries and isolates
  the global monkeypatch per test.
- `tests/const.py` — shared seed constants.
