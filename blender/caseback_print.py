# The 5057G's caseback print: "Cortina Watch / 50th Anniversary / Since 1972" in translucent white on
# the inside of the sapphire caseback. Typeface and layout measured on the caseback photograph
# (AS…--4): an old-style serif with descending 9 and 7 (Hoefler Text matches it, as the SJX close-ups
# show), em 3.03 mm; baselines and centres fitted to the print where it reads cleanly over the gold rotor
# ("niversary", "1972") and over the plate ("Cortina Watch"). Photo-view mm (seen from the back,
# x right); build_5057.py maps it on with the movement's planar UVs.
#   python3 blender/caseback_print.py   ->  blender/textures/caseback_print_5057G.png (white, alpha = print)
# The 5057R (1997) has "CORTINA JUBILEE WATCH" in black serif capitals round the window's edge, tops
# toward the centre, counter-clockwise from about nine o'clock (seen from the back) round the bottom to
# about four; on its caseback photo "TINA" stands by the train bridge's "240/164" and "JUBILEE" over
# the balance:
#   VARIANT=5057R python3 blender/caseback_print.py  ->  caseback_print_5057R.png (black, alpha = print)
import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = ["/System/Library/Fonts/Supplemental/Hoefler Text.ttc", "/System/Library/Fonts/Supplemental/Times New Roman.ttf"]
FONT = next(f for f in FONTS if os.path.exists(f))
R = 14.06            # texture spans [-R, R] mm, as the movement textures
N = 2048
EM = 3.025           # mm
OPACITY = 0.45       # translucent, as photographed: faint over the silver, clearer over the gold rotor
LINES = [            # (text or (main, superscript, rest), baseline y, centre x), photo-view mm
    ("Cortina Watch", 1.7, 0.65),
    (("50", "th", " Anniversary"), -1.075, 0.65),
    ("Since 1972", -4.15, 0.7),
]


ARC = dict(text="CORTINA JUBILEE WATCH", cap=1.85, baseline_r=12.95, start=176.0, end=362.0, opacity=0.93,
           font="/System/Library/Fonts/Supplemental/Times New Roman.ttf")


def main_arc():
    """Capitals set round the window, tops toward the centre, counter-clockwise as seen from the back."""
    k = N / (2 * R)
    ss = 4                                    # draw each letter large, then scale down (crisp)
    a = Image.new("L", (N, N), 0)
    f = ImageFont.truetype(ARC["font"], round(ARC["cap"] / 0.66 * k * ss))
    d0 = ImageDraw.Draw(Image.new("L", (8, 8)))
    text = ARC["text"]
    widths = [d0.textlength(ch, font=f) / ss / k for ch in text]            # mm
    span = math.radians(ARC["end"] - ARC["start"]) * ARC["baseline_r"]      # mm of arc
    track = (span - sum(widths)) / (len(text) - 1)
    print(f"arc {span:.1f} mm, letters {sum(widths):.1f} mm, tracking {track:.2f} mm")
    s_ = 0.0
    for ch, w in zip(text, widths):
        if ch != " ":
            th = math.radians(ARC["start"]) + (s_ + w / 2) / ARC["baseline_r"]   # centre of the letter
            g = Image.new("L", (int(w * k * ss) + 40, int(ARC["cap"] * 1.6 * k * ss)), 0)
            dg = ImageDraw.Draw(g)
            dg.text((g.width / 2, g.height * 0.8), ch, font=f, fill=255, anchor="ms")
            # its up points to the centre: rotate by (th + 90°), scale down, paste centred on the arc
            g = g.rotate(math.degrees(th) + 90, resample=Image.BICUBIC, expand=True)
            g = g.resize((max(1, g.width // ss), max(1, g.height // ss)), Image.LANCZOS)
            # the letter's baseline sits at 0.8 of its box's height, so the box's centre is 0.3 of that
            # height above the baseline: inward, toward the window's centre
            inward = ARC["cap"] * 1.6 * 0.3
            cx_mm = (ARC["baseline_r"] - inward) * math.cos(th)
            cy_mm = (ARC["baseline_r"] - inward) * math.sin(th)
            px, py = (cx_mm + R) * k - g.width / 2, (R - cy_mm) * k - g.height / 2
            a.paste(255, (int(round(px)), int(round(py))), g)
        s_ += w + track
    a = a.point(lambda v: int(v * ARC["opacity"]))
    out = Image.merge("RGBA", (Image.new("L", (N, N), 12),) * 3 + (a,))
    path = os.path.join(HERE, "textures", "caseback_print_5057R.png")
    out.save(path)
    print("wrote", path)


def main():
    k = N / (2 * R)
    img = Image.new("L", (N, N), 0)
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, round(EM * k))
    fs = ImageFont.truetype(FONT, round(EM * 0.58 * k))
    for t, yb, cx in LINES:
        px, py = (cx + R) * k, (R - yb) * k
        if isinstance(t, tuple):     # "50", raised "th", " Anniversary"
            a, b, rest = t
            wa, wb, wr = d.textlength(a, font=f), d.textlength(b, font=fs), d.textlength(rest, font=f)
            x = px - (wa + wb + wr) / 2
            d.text((x, py), a, font=f, fill=255, anchor="ls")
            d.text((x + wa, py - EM * 0.40 * k), b, font=fs, fill=255, anchor="ls")
            d.text((x + wa + wb, py), rest, font=f, fill=255, anchor="ls")
        else:
            d.text((px, py), t, font=f, fill=255, anchor="ms")
    a = img.filter(ImageFilter.GaussianBlur(0.6)).point(lambda v: int(v * OPACITY))
    out = Image.merge("RGBA", (Image.new("L", (N, N), 250),) * 3 + (a,))
    path = os.path.join(HERE, "textures", "caseback_print_5057G.png")
    out.save(path)
    print("wrote", path, "font", os.path.basename(FONT))


if __name__ == "__main__":
    main_arc() if os.environ.get("VARIANT") == "5057R" else main()
