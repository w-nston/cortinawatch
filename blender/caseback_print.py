# The 5057G's caseback print: "Cortina Watch / 50th Anniversary / Since 1972" in translucent white on
# the inside of the sapphire caseback. Typeface and layout measured on the caseback photograph
# (AS…--4): an old-style serif with descending 9 and 7 (Hoefler Text matches it, as the SJX close-ups
# show), em 3.03 mm; baselines and centres fitted to the print where it reads cleanly over the gold rotor
# ("niversary", "1972") and over the plate ("Cortina Watch"). Photo-view mm (seen from the back,
# x right); build_5057.py maps it on with the movement's planar UVs.
#   python3 blender/caseback_print.py   ->  blender/textures/caseback_print_5057G.png (white, alpha = print)
import os
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
    main()
