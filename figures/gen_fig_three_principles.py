#!/usr/bin/env python3
"""Generate the 'Three Design Principles' conceptual editorial illustration via Gemini.

Style: New Yorker / Stripe-blog editorial, semi-flat vector, confident linework,
generous negative space. Triptych layout — one panel per principle.
"""
import os
import sys
import time
from pathlib import Path

from google import genai

OUTPUT_DIR = Path(__file__).resolve().parent

# --- Load GEMINI_API_KEY from environment, falling back to a sibling .env file ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    env_path = OUTPUT_DIR.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                API_KEY = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
if not API_KEY:
    print("ERROR: Set GEMINI_API_KEY (env var or .env file).")
    print("  Get a key at: https://aistudio.google.com/apikey")
    sys.exit(1)

MODEL = "gemini-3-pro-image-preview"
client = genai.Client(api_key=API_KEY)

PROMPT = """
1. FRAMING
Create a single clean, modern editorial conceptual illustration in a New Yorker /
Stripe-blog style. It is a horizontal TRIPTYCH: three equal vertical panels side by
side that together visualize the three design principles of a system for supervising
AI research scientists. The mood is calm, intelligent, confident, and quietly witty —
the kind of spot illustration that opens a thoughtful tech essay. Landscape orientation,
roughly 3:2.

2. VISUAL STYLE — EDITORIAL SEMI-FLAT VECTOR
- Semi-flat vector illustration with confident, deliberate linework: clean ink contours
  of even medium weight, a few strokes carrying the whole idea, NOTHING fussy.
- Generous negative space — let the paper breathe; each panel is mostly empty around
  one strong central metaphor.
- Limited, restrained spot-color palette used as FLAT fills (no gradients, no glossy 3D,
  no drop shadows, no photorealism). Subtle paper grain is acceptable.
- Slightly geometric, modernist shapes; gentle imperfection in the linework gives it a
  hand-considered, human feel rather than a corporate clip-art look.
- Light, even, editorial illustration lighting. No lens flares, no neon glow.
- Typography is a clean grotesque/geometric sans-serif, set small and tasteful.
- Overall: looks like it belongs in The New Yorker or on the Stripe engineering blog.

3. COLOR PALETTE (use these exact flat colors, nothing else)
- Paper background: warm off-white cream #F7F3EA (fills the whole canvas, including gutters)
- Ink / linework + most text: deep ink navy #20242E
- Accent A (warm): coral #E8775B
- Accent B (cool): teal-green #2E9E8C
- Accent C (calm): slate blue #5B7DA6
- Accent D (soft): muted gold #E9C16A
Use ink + cream as the base everywhere; sprinkle the accents sparingly. Each panel may
lean on ONE accent as its dominant spot color but the palette stays consistent across
all three panels so the triptych reads as one cohesive piece.

4. LAYOUT
Overall:
- Warm cream background across the entire canvas.
- A small centered header at the very top in ink navy small-caps: "THREE DESIGN PRINCIPLES"
- Three equal-width panels below it, divided by two thin vertical hairlines in ink navy
  (or generous empty gutters). Each panel has a tiny ordinal in its top-left corner:
  "01", "02", "03" in a circle outline.
- Each panel contains, from top to bottom: a large central conceptual illustration
  (occupying most of the panel), then a bold one-line TITLE, then a single thin caption line.

PANEL 01 — dominant accent: teal-green #2E9E8C
- Metaphor: an AI agent kept honest by guardrails and tethered to ground truth.
- Illustration: a small, friendly abstract robot/agent figure (simple rounded head with a
  single dot eye) walking confidently along a clean straight path that is flanked on BOTH
  sides by two parallel guardrails (rails). Above the agent floats a small rounded "claim"
  bubble; a single TAUT vertical line drops from that bubble down to a solid CHECK-MARK SEAL
  (a circle with a check) anchored into a thin horizontal ground line at the bottom — the
  claim is literally wired to the ground. The guardrails are coral #E8775B; the check seal
  is teal-green; the agent and lines are ink navy.
- TITLE (spell EXACTLY): "Guardrailing & Verification"
- CAPTION (spell EXACTLY): "Every claim wired to ground-truth execution."

PANEL 02 — dominant accent: muted gold #E9C16A
- Metaphor: a messy research trajectory crystallizing into structured knowledge.
- Illustration: on the LEFT, a tangled, scribbly knot of looping lines with a couple of
  small dead-end stubs (the messy graph of pivots and dead ends), drawn in light ink navy.
  The tangle flows toward the RIGHT and RESOLVES into a clean, faceted CRYSTAL / GEM made of
  neat geometric facets — or equivalently a tidy node-and-link lattice — drawn crisply and
  filled with muted gold #E9C16A. A clear visual transition from chaos (left) to ordered
  crystal (right). One small node accented in coral #E8775B.
- TITLE (spell EXACTLY): "Crystallizing Insights"
- CAPTION (spell EXACTLY): "Messy trajectories become structured knowledge."

PANEL 03 — dominant accent: slate blue #5B7DA6
- Metaphor: a human researcher calmly overseeing the AI through a clean interface.
- Illustration: a calm seated human figure (simple, minimal, in profile) viewing a clean
  rectangular SCREEN / dashboard panel. On the screen is a SIMPLIFIED, tidy version of the
  exploration graph (a few neat connected dots) rather than walls of text. A large open EYE
  motif is subtly integrated (e.g. the screen frame suggests an eye, or a small eye icon sits
  above). One of the human's hands reaches gently INTO the screen to nudge a single node —
  signalling effortless course-correction. Screen frame and figure in ink navy; the dashboard
  graph in slate blue #5B7DA6; the nudged node in coral #E8775B.
- TITLE (spell EXACTLY): "Total Observability"
- CAPTION (spell EXACTLY): "High-level oversight, zero-friction course-correction."

5. CONNECTIONS / RELATIONSHIPS
- The three panels are visually parallel and balanced: same illustration size, same title
  placement, same caption placement, consistent line weight and palette across all three.
- Within Panel 01, the single taut tether line connecting the floating claim bubble to the
  ground check-seal is the key relationship — keep it straight and prominent.
- Within Panel 02, show clear left-to-right flow from tangle to crystal.
- Within Panel 03, show the hand-to-node nudge connection clearly.

6. CONSTRAINTS (what NOT to do)
- Spell every title and caption EXACTLY as written above. No other text, no gibberish text,
  no lorem ipsum, no extra labels, no watermark, no signature.
- NO emoji. NO clip-art icons. NO stock-photo look. NO 3D render, NO glossy gradients,
  NO drop shadows, NO neon glow, NO photorealism.
- Do NOT crowd the panels — preserve generous negative space.
- Keep strictly to the listed palette colors.
- Keep linework confident and clean, not sketchy-messy (except the intentional tangle in
  Panel 02, which still reads as deliberate).
"""


def generate_image(prompt_text, attempt_num):
    print(f"\n{'='*60}\nAttempt {attempt_num}\n{'='*60}")
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt_text,
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        output_path = OUTPUT_DIR / f"fig_three_principles_attempt{attempt_num}.png"
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                output_path.write_bytes(part.inline_data.data)
                print(f"Saved: {output_path} ({output_path.stat().st_size:,} bytes)")
                return str(output_path)
            elif part.text:
                print(f"Text: {part.text[:300]}")
        print("WARNING: No image in response")
        return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def main():
    results = []
    for i in range(1, 4):
        if i > 1:
            time.sleep(2)
        path = generate_image(PROMPT, i)
        if path:
            results.append(path)
    if not results:
        print("All attempts failed!")
        sys.exit(1)
    print(f"\nGenerated {len(results)} attempts. Review and pick the best.")


if __name__ == "__main__":
    main()
