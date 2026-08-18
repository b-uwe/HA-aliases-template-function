# HA-aliases-template-function

Adds an aliases() template function/filter returning the aliases of an entity, area, or
floor — a sibling of the existing labels() function.

```jinja
{{ aliases('switch.office_shelly') }}      → ['Office Light Switch']
{{ aliases(area_id('Bedroom')) }}          → ['Sleeping Room']
{{ aliases(floor_id('Basement')) }}        → ['Keller', 'Unten', 'Untergeschoss']

{{ aliases(floor_id('Garage'), 'floor') }} → ['Annex', 'Outbuilding', 'Outhouse']
{{ aliases(area_id('Garage'), 'area') }}   → ['Workshop']
```

Aliases are a first-class registry field on entities, areas, and floors, and they are already
user-facing: Assist uses them to match spoken/typed alternate names. But they are readable
**everywhere except from a template**. Core already exposes the neighbouring registry
metadata template authors rely on — `labels()`, `area_id()`, `area_name()`, `floor_id()`,
`floor_name()` — so the alias field is the one obvious gap in that set. `aliases()` closes it.

The function returns a sorted `list[str]` (`[]` when the target is unknown or has no aliases),
registered as both a global and a filter. Dispatch mirrors `labels()`: entity → area → floor —
the three registries that carry an aliases field.

<details>
<summary>Example: alias-review dashboard — new <code>aliases()</code></summary>
... next to the <code>labels()</code> it mirrors

```yaml
type: markdown
content: |-
  ## Alias overview
  <table>
    <tr><th colspan="3">Name</th><th>ID</th><th>Aliases</th><th>Labels</th></tr>
    {% for floor in floors() %}
    <tr>
      <td colspan="3"><b>{{ floor_name(floor) }}</b></td>
      <td>{{ floor }}</td>
      <td>{{ aliases(floor) }}</td>
      <td>{{ labels(floor) }}</td>
    </tr>
    {% for area in floor_areas(floor) %}
    <tr>
      <td>↳</td>
      <td colspan="2"><b>{{ area_name(area) }}</b></td>
      <td>{{ area }}</td>
      <td>{{ aliases(area) }}</td>
      <td>{{ labels(area) }}</td>
    </tr>
    {% for entity in area_entities(area) %}
    <tr>
      <td>&#160;</td>
      <td>↳</td>
      <td>{{ state_attr(entity, 'friendly_name') or entity }}</td>
      <td>{{ entity }}</td>
      <td>{{ aliases(entity) }}</td>
      <td>{{ labels(entity) }}</td>
    </tr>
    {% endfor %}
    {% endfor %}
    {% endfor %}
  </table>
```
</details>

This is a HACS version of [#176863](https://github.com/home-assistant/core/pull/176863) which didn't make it into Core.