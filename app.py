# Week 5 - Fireworks Generative Poster (Streamlit version)
# Concepts: from Colab notebook to web app, generative art with randomness + seed
# Style: black night sky, round fireworks that radiate from a bright center point

import random, math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import hsv_to_rgb, rgb_to_hsv
from matplotlib.collections import LineCollection
import streamlit as st

W = 0.75   # poster width in data units (height is 1.0) -> keeps circles round on a 6x8 figure


# Palette generator (HSV): returns bright base colors, spread out so bursts differ
def make_palette(k=6, mode="neon"):
    cols = []
    start = random.random()
    for i in range(k):
        if mode == "neon":        # saturated, electric colors across the whole hue wheel
            h = (start + i / k) % 1.0; s = random.uniform(0.7, 1.0)
        elif mode == "gold":      # warm gold / amber / red-orange, like classic fireworks
            h = random.uniform(0.0, 0.13); s = random.uniform(0.5, 0.9)
        elif mode == "ice":       # cool blue / cyan / violet
            h = random.uniform(0.5, 0.78); s = random.uniform(0.3, 0.85)
        elif mode == "sunset":    # pink / orange / purple
            h = (random.choice([0.0, 0.03, 0.08, 0.85, 0.9]) + random.uniform(-0.02, 0.02)) % 1.0
            s = random.uniform(0.6, 1.0)
        else:                     # rainbow: evenly spread hues
            h = (i / k + random.uniform(-0.03, 0.03)) % 1.0; s = random.uniform(0.7, 1.0)
        cols.append(tuple(hsv_to_rgb([h, s, 1.0])))
    random.shuffle(cols)
    return cols


# Second tone for a color: hue shifted a little, so one burst has two colors
def shift_hue(color, dh):
    h, s, v = rgb_to_hsv(np.array(color))
    return tuple(hsv_to_rgb([(h + dh) % 1.0, s, v]))


def mix_white(color, amount):
    return tuple(np.array(color) * (1 - amount) + amount)


# Bright glowing core: this is the "center point" of the firework
def core(ax, c, color, scale):
    cx, cy = c
    ax.scatter([cx], [cy], s=3200 * scale, color=color, alpha=0.06, linewidths=0)
    ax.scatter([cx], [cy], s=1300 * scale, color=color, alpha=0.12, linewidths=0)
    ax.scatter([cx], [cy], s=450 * scale, color=mix_white(color, 0.4), alpha=0.25, linewidths=0)
    ax.scatter([cx], [cy], s=150 * scale, color=mix_white(color, 0.7), alpha=0.55, linewidths=0)
    ax.scatter([cx], [cy], s=45 * scale, color="white", alpha=0.95, linewidths=0)


# Style 1: chrysanthemum / star - rays from the center, glowing tips, sparks along each ray
def burst_rays(ax, c, R, n_rays, length, color, color2, rng, star=False):
    cx, cy = c
    if star:
        n_rays = max(8, n_rays // 4)
    angles = np.linspace(0, 2 * math.pi, n_rays, endpoint=False) + rng.uniform(0, 2 * math.pi)
    angles += rng.normal(0, 0.015 if star else 0.03, n_rays)
    reach = R * rng.uniform(0.82, 1.0, n_rays)
    dx, dy = np.cos(angles), np.sin(angles)

    # long rays + (for the round style) short inner rays that fill the hub with light
    rays = [(dx[i], dy[i], reach[i], 0.04) for i in range(n_rays)]
    if not star:
        a2 = rng.uniform(0, 2 * math.pi, n_rays // 2)
        rays += [(math.cos(a), math.sin(a), R * rng.uniform(0.25, 0.5), 0.0) for a in a2]

    steps = 12
    segs, cols = [], []
    for ux, uy, rr, t0 in rays:
        ts = np.linspace(max(t0, 1.0 - length) if rr > 0.6 * R else 0.0, 1.0, steps)
        xs, ys = cx + ux * rr * ts, cy + uy * rr * ts
        for j in range(steps - 1):
            f = (j + 1) / (steps - 1)
            col = np.array(mix_white(color, 0.5 * (1 - f))) * (1 - f) + np.array(color2) * f   # bright hub -> color -> color2
            segs.append([(xs[j], ys[j]), (xs[j + 1], ys[j + 1])])
            cols.append((*col, 0.55 + 0.4 * f))
    glow = [(*c_[:3], c_[3] * 0.15) for c_ in cols]
    ax.add_collection(LineCollection(segs, colors=glow, linewidths=5.0 if star else 3.0, capstyle="round"))
    ax.add_collection(LineCollection(segs, colors=cols, linewidths=2.0 if star else 0.9, capstyle="round"))

    # sparks scattered along the rays (like tiny beads)
    k = n_rays * 2
    idx = rng.integers(0, n_rays, k)
    tt = rng.uniform(0.3, 1.0, k)
    ax.scatter(cx + dx[idx] * reach[idx] * tt, cy + dy[idx] * reach[idx] * tt,
               s=rng.uniform(1, 4, k), color=color2, alpha=0.8, linewidths=0)

    # glowing tips
    tx, ty = cx + dx * reach, cy + dy * reach
    ax.scatter(tx, ty, s=(160 if star else 45), color=color2, alpha=0.12, linewidths=0)
    ax.scatter(tx, ty, s=(60 if star else 16), color=color2, alpha=0.35, linewidths=0)
    ax.scatter(tx, ty, s=(14 if star else 4), color="white", alpha=0.95, linewidths=0)


# Style 2: sparkle ball - hundreds of glittering dots filling a sphere
def burst_sparkle(ax, c, R, n_rays, color, color2, rng):
    cx, cy = c
    n = n_rays * 10
    a = rng.uniform(0, 2 * math.pi, n)
    d = R * np.sqrt(rng.uniform(0.0, 1.0, n))
    x, y = cx + d * np.cos(a), cy + d * np.sin(a)
    pick = rng.random(n) < 0.5
    cols = [color if p else color2 for p in pick]
    sz = rng.uniform(0.8, 6, n)
    ax.scatter(x, y, s=sz * 6, color=cols, alpha=0.10, linewidths=0)
    ax.scatter(x, y, s=sz, color=cols, alpha=0.9, linewidths=0)
    ax.scatter(x, y, s=sz * 0.25, color="white", alpha=0.8, linewidths=0)


# One burst: draws the chosen style plus the glowing center
def burst(ax, c, R, n_rays, length, style, color, rng):
    color2 = shift_hue(color, rng.choice([-0.08, 0.08]))
    if style == "sparkle ball":
        burst_sparkle(ax, c, R, n_rays, color, color2, rng)
    elif style == "star":
        burst_rays(ax, c, R, n_rays, length, color, color2, rng, star=True)
    else:
        burst_rays(ax, c, R, n_rays, length, color, color2, rng)
    core(ax, c, color, R / 0.2)


# Place burst centers so that they overlap as little as possible and stay inside the frame
def place_centers(n, radii, rng):
    centers = []
    for i in range(n):
        m = radii[i] + 0.02
        best, best_gap = None, -1e9
        for _ in range(400):
            p = (rng.uniform(m, W - m), rng.uniform(m, 1 - m))
            gap = min([math.dist(p, q) - 0.95 * (radii[i] + radii[j]) for j, q in enumerate(centers)] or [1])
            if gap > best_gap:
                best, best_gap = p, gap
            if gap >= 0:
                break
        centers.append(best)
    return centers


# Main drawing function: returns a figure instead of calling plt.show()
def draw_poster(n_bursts=4, n_rays=90, size=0.17, length=1.0,
                style="mix", palette_mode="neon", seed=0):
    random.seed(seed)
    rng = np.random.default_rng(seed)
    fig, ax = plt.subplots(figsize=(6, 8))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)   # poster fills the whole frame
    fig.patch.set_facecolor("black")
    ax.set_facecolor("black")
    ax.set_xlim(0, W)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # distant stars in the night sky
    n_stars = 90
    ax.scatter(rng.uniform(0, W, n_stars), rng.random(n_stars),
               s=rng.uniform(0.3, 1.8, n_stars), color="white",
               alpha=rng.uniform(0.1, 0.5, n_stars), linewidths=0)

    palette = make_palette(6, mode=palette_mode)
    radii = [size * rng.uniform(0.8, 1.2) for _ in range(n_bursts)]
    centers = place_centers(n_bursts, radii, rng)
    for i, (c, R) in enumerate(zip(centers, radii)):
        s = style if style != "mix" else random.choice(["chrysanthemum", "sparkle ball", "star"])
        burst(ax, c, R, n_rays, length, s, palette[i % len(palette)], rng)

    ax.text(0.04, 0.03, f"Fireworks Poster • {style} • {palette_mode} • seed {seed}",
            transform=ax.transAxes, fontsize=9, color="white", alpha=0.8, weight="bold")
    return fig


# ---------- Streamlit UI ----------
st.set_page_config(page_title="Fireworks Generative Poster", layout="centered")
st.title("Fireworks Generative Poster")
st.caption("Arts and Advanced Big Data | From Colab to the Web")

st.sidebar.header("Controls")
n_bursts = st.sidebar.slider("Bursts", min_value=1, max_value=12, value=4, step=1)
n_rays = st.sidebar.slider("Sparks per burst", min_value=20, max_value=160, value=90, step=2)
size = st.sidebar.slider("Burst size", min_value=0.08, max_value=0.35, value=0.17, step=0.01)
length = st.sidebar.slider("Ray length", min_value=0.30, max_value=1.00, value=1.00, step=0.05)
style = st.sidebar.selectbox("Burst style", ["mix", "chrysanthemum", "sparkle ball", "star"])
palette_mode = st.sidebar.selectbox("Palette mode", ["neon", "gold", "ice", "sunset", "rainbow"])
seed = st.sidebar.slider("Seed", min_value=0, max_value=9999, value=0, step=1)

fig = draw_poster(n_bursts, n_rays, size, length, style, palette_mode, seed)
st.pyplot(fig)
