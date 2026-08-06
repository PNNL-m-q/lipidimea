# lipidimea-review

Interactive GUI for reviewing lipidimea DIA results. Step through feature
groups, inspect diagnostic plots, mark bad items for deletion, then commit
or export.

## Launch

```sh
lipidimea-review                  # open blank; use "load results" to pick a DB
lipidimea-review path/to.db       # open with database pre-loaded
```

## Layout

- **Toolbar (top):** `load results` / `save results` / `export results`,
  plus `delete unannotated` above the group panel.
- **Group panel (left):** one row per DIA feature group.
- **Plot stack (middle):** MS1, XIC, ATD, MS2 for the selected group.
- **Feature panel (top right):** DIA precursors in the selected group.
- **Annotation panel (bottom right):** lipid annotations for the group.
- **Status bar (bottom):** DB path, pending-deletion counts, active panel.

## Selecting things

- Click any row in the group panel to load its plots and populate the
  feature / annotation panels.
- Selecting an annotation highlights its annotated fragments in the MS2
  plot (colored vertical guides) and enriches MS2 hover tooltips with
  fragment labels.
- Each panel has an **ID entry** above it — type an ID, press Enter to
  jump to it.
- Click any column header to sort; click again to reverse.

## Feature display toggles

Each row in the feature panel has a display checkbox (☐ / ☑). Toggling
hides/shows that precursor's traces in the plots. Click the glyph, or
press **d** with the row selected. State resets each time you navigate
to a new group.

## Marking for deletion

The active panel is outlined in blue. Switch active panel with:

- **g** — group panel
- **f** — feature panel
- **l** — lipid annotation panel

Then in the active panel:

- **↑ / ↓** — move selection
- **Delete / Backspace** — toggle deletion mark on the selected row

Marked rows stay visible but are greyed out. Toggle again to unmark.
**Ctrl+Z** undoes the last mark.

The `delete unannotated` button bulk-marks every group with zero
annotations (as of DB load).

Nothing is written to the database until you save.

## Plots

- Each plot has its own zoom/pan/home/save toolbar below it.
- Hover any peak in MS1 or MS2 to see its m/z. If a lipid annotation is
  active and the peak matches an annotated fragment (within tolerance),
  the fragment label — and a `[diagnostic]` tag when applicable — is
  also shown.
- MS2 is a mirror plot: DIA precursors above the axis, DDA below.
  Intensities are normalized per side to max=1.

## Toolbar actions

- **load results** — pick a database file. Prompts to discard any
  pending deletions.
- **save results** (Ctrl+S) — commit all pending deletions to the
  database. Irreversible. Disabled when nothing is pending.
- **export results** (Ctrl+E) — write a CSV of retained feature groups
  and annotations at the current review state. Does not require a save
  first.

## Keyboard shortcut summary

| key                | action                                   |
| ------------------ | ---------------------------------------- |
| `g` / `f` / `l`    | switch active panel                      |
| `↑` / `↓`          | move selection in active panel           |
| `Delete` / `Backspace` | toggle deletion mark on selected row |
| `d`                | toggle display on selected feature row   |
| `Ctrl+Z`           | undo last deletion mark                  |
| `Ctrl+S`           | save (commit pending deletions)          |
| `Ctrl+E`           | export CSV                               |
```