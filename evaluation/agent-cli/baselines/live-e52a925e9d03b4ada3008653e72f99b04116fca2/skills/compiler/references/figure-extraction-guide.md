# Figure Extraction Guide — Reading Plots, Diagrams, and Samples

Load this when an input contains figures whose information is not available as text. The goal
is to turn pixels into structured ARA evidence **honestly**: exact where the source is exact,
explicitly approximate where you are reading off a plot, and structural (not numeric) where the
figure is a diagram.

The governing rule (Critical Rule #11): read figures by looking at them, mark estimates as
estimates, and never fabricate a data table for a figure that does not contain one.

---

## 0. Decide whether you even need to crop

Try reading the figure from the rendered PDF page first — the Read tool renders PDF pages and
displays images visually. Only fall back to rendering/cropping (Section 2) when the figure is:
- too small or dense to read values reliably,
- one panel in a multi-panel figure you need to isolate,
- overlapping with text/other figures, or
- in a vector format you want at higher resolution.

Cropping is a means to *see better*, not a required step.

---

## 1. Classify before you read

| Type | What it carries | ARA destination | Do NOT |
|------|-----------------|-----------------|--------|
| `quantitative_plot` | numbers on axes (line/bar/scatter/box/hist/heatmap) | `evidence/figures/` data table + trend summary | invent points you cannot see |
| `diagram` | structure: components + connections | `evidence/figures/` visual description **and** `logic/solution/architecture.md` | build a numeric table |
| `qualitative_sample` | a demonstrated behavior/artifact | `evidence/figures/` visual description, tied to a claim/gap | claim measurements |
| `mixed` | several of the above in one figure | split per panel, classify each | collapse panels together |

If you are unsure, classify by asking "could I, in principle, read a number off an axis here?"
If no, it is not a `quantitative_plot`.

---

## 2. Rendering and cropping a figure (when needed)

The skill allows `Bash(python *)`. Prefer **PyMuPDF** (`fitz`) — no system dependencies, fast,
and lets you crop a sub-region. `pdf2image` is a fine alternative when you only need full pages.

**Save every render as the evidence screenshot.** The cropped PNG you produce for a table/figure
is not transient — save it into the artifact next to its markdown (`evidence/figures/figureN.png`,
`evidence/tables/tableN.png`). Crop to the object's region so the screenshot shows just that
table/figure. Every numbered table and figure must end up with a saved `.png`.

### 2a. Render a whole page to PNG (PyMuPDF)

```python
import fitz  # PyMuPDF

doc = fitz.open("paper.pdf")
page = doc[6]                       # 0-indexed; page 7 in the PDF
pix = page.get_pixmap(dpi=200)      # bump dpi for dense plots (200–300)
pix.save("page7.png")
```

Then Read `page7.png` as an image.

### 2b. Crop a single figure region (PyMuPDF)

Coordinates are in PDF points (72 pt = 1 inch), origin at the top-left of the page. Find the
rough box by eye from the full-page render, then crop with a `clip` rectangle:

```python
import fitz

doc = fitz.open("paper.pdf")
page = doc[6]
# clip = (x0, y0, x1, y1) in points — the bounding box of the figure on the page
clip = fitz.Rect(60, 90, 540, 360)
pix = page.get_pixmap(dpi=300, clip=clip)
pix.save("fig4_cropped.png")
```

Increase `dpi` if axis ticks or legends are still unreadable. Re-Read the crop and iterate.

### 2c. Full-page fallback (pdf2image)

```python
from pdf2image import convert_from_path

pages = convert_from_path("paper.pdf", dpi=200, first_page=7, last_page=7)
pages[0].save("page7.png")
```

### 2d. Standalone image inputs

If given `.png`/`.jpg`/`.svg`/exported plots directly, Read them as-is. For `.svg`, the text
labels are often in the XML — `Grep` the file for axis labels and series names to corroborate
what you read visually.

---

## 3. Reading a quantitative plot

1. **Axes first.** Record both axis labels, units, and **scale (linear vs log)**. A log axis
   read as linear silently corrupts every value — check tick spacing (equal multiplicative
   gaps ⇒ log).
2. **Ranges and gridlines.** Note the axis min/max and any gridlines; they are your ruler.
3. **Prefer printed values.** If the plot has data labels, or the text/caption states the key
   numbers, use those and set `extraction method: exact_from_labels`.
4. **Otherwise estimate.** Read each point against the gridlines, mark it `≈`, and set
   `extraction method: digitized_estimate` with a `reading confidence`.
5. **Always capture the trend.** Even when exact points are unreadable, the *shape* is real
   evidence: monotonic? plateau? crossover at x≈?? which series is on top? variance bands?
6. **Series and legend.** One column per series; name them exactly as the legend does.

Confidence rubric:
- `high` — clean axes, gridlines, few points, or printed labels
- `medium` — readable but interpolated between gridlines
- `low` — dense/overlapping/blurred; record the trend and say points are unreliable

### Worked example — line plot

Source: a 2-series accuracy-vs-epochs line plot, no data labels, linear axes.

```markdown
# Figure 4: Validation accuracy vs. training epochs
- **Source**: Figure 4, Section 5.2
- **Caption**: "Validation accuracy over training for Ours vs. Baseline."
- **Figure type**: quantitative_plot
- **Extraction method**: digitized_estimate
- **Reading confidence**: medium
- **Plot kind**: line
- **Axes**: X = epoch (count, linear), Y = top-1 accuracy (%, linear)

| Epoch | Ours (%) | Baseline (%) |
|-------|----------|--------------|
| 10    | ≈62      | ≈58          |
| 30    | ≈74      | ≈66          |
| 50    | ≈78      | ≈69          |

## Trend summary
Both rise monotonically and plateau by ~epoch 40. Ours is above Baseline at every read point;
the gap widens from ≈4 pts (epoch 10) to ≈9 pts (epoch 50). Exact endpoints unreadable — see
evidence/tables/ for any reported final numbers.
```

> Note the discipline: the claim "Ours > Baseline, gap widens" is well supported even though
> every individual number is approximate. Put the directional fact in the claim's
> `Evidence basis`; do not promote "≈78%" into an exact result.

---

## 4. Reading a diagram

Do not build a data table. Capture structure, then mirror it into `architecture.md`.

```markdown
# Figure 2: Model architecture
- **Source**: Figure 2, Section 3.1
- **Caption**: "Overview of the proposed two-stage encoder."
- **Figure type**: diagram
- **Extraction method**: visual_description
- **Reading confidence**: high

## Visual description
- **Components**: Tokenizer → Stage-A encoder (6 blocks) → Cross-attn bridge → Stage-B decoder → Head
- **Connections**: residual skip from Stage-A output to Cross-attn bridge; dashed arrow = optional auxiliary loss path
- **Annotations**: blue boxes = trainable, grey = frozen; the bridge is the paper's novel block
- **What it conveys**: the contribution sits in the cross-attn bridge, not the encoders
```

The component graph here becomes the backbone of `logic/solution/architecture.md`.

---

## 5. Reading a qualitative sample

```markdown
# Figure 6: Failure cases on out-of-distribution inputs
- **Source**: Figure 6, Appendix C
- **Caption**: "Representative failures under distribution shift."
- **Figure type**: qualitative_sample
- **Extraction method**: visual_description
- **Reading confidence**: high

## Visual description
- **Shows**: 4 input/output pairs where the model mislabels rotated objects
- **Demonstrates**: the rotation-sensitivity failure mode
- **Supports**: G2 (robustness gap), and is the qualitative basis behind C04's limitation clause
```

No numbers — but this is genuine evidence for a gap/limitation and must be tied to a claim or gap ID.

---

## 6. Common traps

- **Log axes** read as linear — the single most damaging error. Check tick spacing every time.
- **Secondary (right-hand) Y-axis** — dual-axis plots have two scales; map each series to the
  correct one.
- **Truncated / broken axes** (axis not starting at 0) — exaggerates differences; note it in
  the trend summary so claims are not overstated.
- **Error bars / shaded bands** — capture them; they bound how strong a claim can be.
- **Color-only series distinction** — name series by legend text, not color, so the table is
  unambiguous.
- **Stacked vs grouped bars** — stacked totals are cumulative; do not read a stacked segment as
  an absolute value.
- **Subset panels** — a single panel pulled from a multi-panel figure is a derived view; name it
  `derived_`/`subset_` and cite the parent figure, per the evidence naming rules.

---

## 7. Honesty checklist (before writing the figure file)

- [ ] Figure type classified, and the file matches it (plot ⇒ table+trend; diagram/sample ⇒ visual description)
- [ ] `Extraction method` and `Reading confidence` set, and consistent with the content
- [ ] Every estimated number marked `≈`; nothing estimated is labeled `exact_from_labels`
- [ ] Axis scale (linear/log) recorded for plots
- [ ] No fabricated table for a diagram or qualitative sample
- [ ] Unreadable figure stated as `reading confidence: low` with a trend summary, not invented points
- [ ] Diagram structure mirrored into `logic/solution/architecture.md`
- [ ] Qualitative sample tied to a claim or gap ID
