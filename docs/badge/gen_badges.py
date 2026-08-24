#!/usr/bin/env python3
"""Generate candidate ARA paper badges with Gemini image generation.

Usage:  GEMINI_API_KEY=... python gen_badges.py [--only 3,7]
Outputs badge_XX_<slug>.png next to this script.
"""
import os, sys, time
from google import genai

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("ERROR: set GEMINI_API_KEY")

MODEL = "gemini-3-pro-image-preview"
OUT = os.path.dirname(os.path.abspath(__file__))
client = genai.Client(api_key=API_KEY)

COMMON = """
Design a small BADGE for the top-right corner of an academic paper PDF. It certifies the paper
ships with an "ARA" — Agent-Native Research Artifact — a MACHINE-READABLE research artifact.

DIRECTION: the badge is a REAL, PHYSICAL PAPER HANG TAG rendered as a clean, premium product
illustration (Muji / Aesop / Apple packaging calm). The second attached image is the approved
tag SHAPE and composition: landscape rectangular shipping tag, left end angled/pointed with
the punched hole and eyelet, short twine loop, "{ARA}" printed large and centered on the body.
KEEP THAT SHAPE AND COMPOSITION. Change only the color scheme as described below.

COLOR SCHEME — WHITE TAG, PEACH ACCENT:
- The tag card stock is WHITE / very soft off-white (#FFFFFF to #FAF8F5), so it must be
  separated from the pure white canvas by a soft single drop shadow and a faint edge; a subtle
  paper grain is fine.
- The brand accent is warm peach-orange #e8a878. Use it EXACTLY as the concept says — as the
  one accent element. Never more peach than the concept allows.
- Print: "{ARA}" in deep ink #1a1530, slab-serif / typewriter caps (American Typewriter feel),
  letter-spaced, SPELL EXACTLY. A tiny secondary line only where the concept says, spelled
  EXACTLY. No other text.

ORIENTATION: perfectly horizontal and level — NO tilt, NO rotation. The twine, if present, is
short and tidy.

CANVAS: square, pure white #FFFFFF background, tag centered, tag about 65-70% of the width.
NO scene, NO table, NO hands, NO other objects. Must read at 1.5 cm wide when printed.
The first attached image is the brand mark, for spirit only.
"""

BADGES = [
    ("final_a", """
CONCEPT (FINAL): Reproduce the second attached image as faithfully as possible — same tag
shape, same white card, same brass eyelet, same "{ARA}" typography and size, same small peach
square superscript — with exactly ONE change: REMOVE THE TWINE / STRING entirely. Just the
empty eyelet. Nothing else changes."""),
    ("final_b", """
CONCEPT (FINAL): Reproduce the second attached image as faithfully as possible — same tag
shape, same white card, same brass eyelet, same "{ARA}" typography and size, same small peach
square superscript — with exactly ONE change: REMOVE THE TWINE / STRING entirely. Just the
empty eyelet. Nothing else changes. Keep the drop shadow soft and the edges crisp."""),
    ("final_c", """
CONCEPT (FINAL): Reproduce the second attached image as faithfully as possible — same tag
shape, same white card, same brass eyelet, same "{ARA}" typography and size, same small peach
square superscript — with exactly ONE change: REMOVE THE TWINE / STRING entirely. Just the
empty eyelet. Nothing else changes. Render at the highest crispness you can."""),
]

def gen(idx, slug, concept):
    prompt = COMMON + "\n" + concept
    name = f"badge_{idx:02d}_{slug}.png"
    path = os.path.join(OUT, name)
    for attempt in range(1, 4):
        try:
            ref = genai.types.Part.from_bytes(
                data=open(os.path.join(OUT, "ref_mark.png"), "rb").read(), mime_type="image/png")
            resp = client.models.generate_content(
                model=MODEL, contents=[prompt, "Image 1 — brand mark (spirit only):", ref,
                          "Image 2 — approved final design (remove the string only):",
                          genai.types.Part.from_bytes(data=open(os.path.join(OUT, "ref_round5.png"), "rb").read(), mime_type="image/png")],
                config=genai.types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                    image_config=genai.types.ImageConfig(aspect_ratio="1:1"),
                ),
            )
            for part in resp.candidates[0].content.parts:
                if part.inline_data:
                    with open(path, "wb") as f:
                        f.write(part.inline_data.data)
                    print(f"saved {name} ({os.path.getsize(path):,} B)")
                    return path
            print(f"{name}: no image (attempt {attempt})")
        except Exception as e:
            print(f"{name}: error attempt {attempt}: {e}")
            time.sleep(3)
    return None


if __name__ == "__main__":
    only = None
    if "--only" in sys.argv:
        only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    for i, (slug, concept) in enumerate(BADGES, 1):
        if only and i not in only:
            continue
        gen(i, slug, concept)
        time.sleep(1)
