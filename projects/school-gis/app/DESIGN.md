# School Neighborhood GIS Design System

This document is the shared design contract for the School Neighborhood GIS app.
It is written for both human contributors and AI agents.

The product goal is not "pretty UI."
The product goal is a map-first learning tool where students can:

1. load a few relevant public layers,
2. add their own point, line, and polygon observations,
3. overlap those layers,
4. explain what makes their neighborhood distinct.

## 1. Product Intent

- Build a student-first educational webGIS.
- Teach overlap analysis through direct use, not long explanation.
- Keep the interface practical, calm, and easy to operate on phones and tablets.
- Optimize for understanding, speed, and map visibility before visual decoration.

## 2. Primary Users

### Students

- Students are the main audience.
- Assume they do not know GIS terms.
- The default flow must be obvious on first open.
- The core flow is:
  - turn on a public layer,
  - add a student layer,
  - compare layers,
  - write one short conclusion.

### Teachers

- Teachers are secondary users.
- Teacher tools should be hidden behind advanced panels.
- Teacher tools must not complicate the default student view.

## 3. Core UX Principles

- The map is always the main surface.
- Each screen should emphasize one primary action.
- Do not expose raw GIS jargon in the default student interface.
- Advanced import tools belong in collapsible sections.
- Drawing on the map is the primary student input mode.
- Public layers should be curated, not exhaustive.
- The default state should never feel empty or confusing.

## 4. Visual Direction

Keywords:

- field lab
- civic map
- calm
- precise
- practical

Visual tone:

- bright surfaces
- deep green ink
- restrained warm accent
- no flashy gradients or glow-heavy aesthetics

## 5. Tokens

### Typography

- Primary font: IBM Plex Sans KR
- Strong headings, compact body copy
- Short instructional text
- Avoid large blocks of explanatory prose

### Color

Recommended token set:

```css
:root {
  --bg: #f5f7f2;
  --panel: #ffffff;
  --panel-soft: #eef3ed;
  --ink: #112720;
  --ink-soft: #4d655c;
  --line: rgba(17, 39, 32, 0.12);
  --primary: #1f6a57;
  --primary-soft: rgba(31, 106, 87, 0.1);
  --accent: #f2c14e;
  --danger: #c94558;
  --warn: #dd6b39;
  --success: #238b68;
  --data-blue: #1d78c8;
}
```

Rules:

- Use bright map-tool surfaces.
- Keep accent use restrained.
- Public statistics may use blue family colors.
- Student-created layers may use warmer contrasting colors.

### Shape

- Large card radius: 22px
- Standard card radius: 16px
- Pills and segmented controls may use full rounded corners
- Avoid oversized soft blobs or playful rounded cartoon shapes

### Spacing

- Use 4px spacing scale
- Standard card padding: 16px to 20px
- Reduce vertical waste aggressively on mobile

## 6. Layout Rules

### Desktop

- Use a slim left panel and a dominant map area.
- The map should visually own the page.
- The sidebar is a task panel, not the main content.
- Keep the header compact.

### Tablet

- Preserve map priority.
- Avoid deep stacked panels.
- Keep layer actions reachable without long scroll.

### Mobile

- Show the map immediately on first screen.
- Use a bottom sheet or compact side sheet for tools.
- Keep one clear primary action visible.
- Avoid layouts where the user must scroll through cards before seeing the map.

## 7. Map Rules

- Default center is the school, not the current location.
- Current location is optional support, not the primary anchor.
- "Return to school" must always be easy to find.
- The school radius should be visible in school mode.
- Keep the legend small and readable.

## 8. Public Layer Rules

- The first job of the public layer panel is loading real data.
- Example layers are secondary and should be visually demoted.
- In school mode, "Load real statistics for this school area" should come first.
- Students should not type administrative codes in the default path.
- Use interpretation-friendly labels such as:
  - people density
  - average age
  - business concentration

## 9. Student Layer Rules

- Default student input is direct drawing:
  - point
  - line
  - polygon
- File import is advanced-only.
- Keep student properties minimal:
  - layer name
  - geometry type
  - color
  - note
  - importance
- While drawing, hide unnecessary controls and focus on the current step.

## 10. Interaction Rules

- Use action-first labels.
- Do not rely on color alone for state.
- Show pending and error states clearly.
- Error messages must explain what to do next.

Good examples:

- Loading SGIS statistics for the selected school area.
- Could not determine the administrative area for this school. Check the school location and try again.
- Local SGIS proxy was not found. Restart the local server and try again.

## 11. Language Rules

- Write student-facing copy in plain Korean.
- Avoid technical labels unless they are behind advanced controls.
- Keep instructional text short and directional.
- Prefer "what to do next" over abstract explanation.

## 12. Accessibility

- Minimum touch target height: 44px
- Maintain strong text contrast
- Do not communicate state by color alone
- Keep map controls usable on touch devices

## 13. Motion

- Motion should support orientation, not decoration.
- Allowed motion:
  - sheet open and close
  - light card state transitions
  - map pan and fly transitions
- Avoid noisy or continuous motion.

## 14. Anti-Patterns

Do not ship these patterns:

- empty map plus empty panel on first load
- raw lat/lng or adm_cd as the default student path
- long hero sections that push the map down
- too many layers enabled by default
- advanced teacher tools mixed into the main student flow
- visually loud gradients that reduce information clarity

## 15. Implementation Guidance For AI Agents

- Any new UI change should preserve or increase visible map area.
- Validate new ideas against the student-first flow before implementing.
- Add advanced controls only behind collapsible panels.
- Prefer direct manipulation over file-oriented workflows.
- When in doubt, choose clarity and map visibility over visual flair.

## 16. Current Design Target

The current target student journey is:

1. find the school,
2. view the school neighborhood,
3. load real SGIS statistics for the school area,
4. draw points, lines, and polygons,
5. compare layers,
6. write one short regional interpretation.
