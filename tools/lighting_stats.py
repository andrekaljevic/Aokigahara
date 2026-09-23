#!/usr/bin/env python3
"""Measure the lighting character of rendered frames, engine-agnostically.

The owner's most valued result from the UE5.8 attempt was its natural forest lighting: dappled
sun on the floor, a dark sky-occluded understorey, bright sky gaps, cool shadows and warm
highlights. This tool turns that look into numbers so that renders from any engine can be compared
against the UE5.8 baseline in renders/ue58_baseline/ instead of by eye alone.

Usage:
    python3 tools/lighting_stats.py IMAGE [IMAGE ...] [--json OUT.json]

Requires NumPy and Pillow. Every metric is computed on linear-light Rec. 709 luminance decoded
from sRGB. The frame is split into an upper band (rows above 40 %, where sky gaps appear) and a
ground band (rows below 40 %).

Metrics:
    log_avg_luminance   geometric-mean luminance, the usual "key" of an exposure
    p01 ... p99         luminance percentiles
    stops_p01_p99       dynamic range in stops between the 1st and 99th percentile
    sunfleck_fraction   share of ground-band pixels brighter than 4 x the ground median (dappled sun)
    sky_fraction        share of upper-band pixels that are bright and blue-dominant (sky gaps)
    shadow_blue_ratio   mean B/R in the darkest 20 % of pixels (sky-lit shadows read cool, > 1)
    highlight_blue_ratio mean B/R in the brightest 10 % of non-sky ground pixels (sun reads warm, < 1)
    clipped_fraction    share of pixels with any channel at 250 or above in 8-bit sRGB
"""

import argparse
import json
import sys

import numpy as np
from PIL import Image

EPS = 1e-4


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def measure(path):
    rgb8 = np.asarray(Image.open(path).convert("RGB"))
    rgb = srgb_to_linear(rgb8.astype(np.float64) / 255.0)
    lum = rgb @ np.array([0.2126, 0.7152, 0.0722])
    h = lum.shape[0]
    split = int(h * 0.4)
    upper, ground = lum[:split], lum[split:]
    r, b = rgb[..., 0], rgb[..., 2]
    blue_ratio = (b + EPS) / (r + EPS)

    pct = {f"p{p:02d}": float(np.percentile(lum, p)) for p in (1, 5, 25, 50, 75, 95, 99)}

    ground_median = float(np.median(ground))
    sunfleck = float(np.mean(ground > 4.0 * max(ground_median, EPS)))

    upper_bright = upper > np.percentile(lum, 99) * 0.5
    upper_blue = blue_ratio[:split] > 1.0
    sky = float(np.mean(upper_bright & upper_blue))

    dark_cut = np.percentile(lum, 20)
    shadow_blue = float(np.mean(blue_ratio[lum <= dark_cut]))

    g_blue = blue_ratio[split:]
    g_bright_cut = np.percentile(ground, 90)
    highlight_blue = float(np.mean(g_blue[ground >= g_bright_cut]))

    return {
        "file": path,
        "size": [int(rgb8.shape[1]), int(rgb8.shape[0])],
        "log_avg_luminance": float(np.exp(np.mean(np.log(lum + EPS)))),
        **pct,
        "stops_p01_p99": float(np.log2((pct["p99"] + EPS) / (pct["p01"] + EPS))),
        "sunfleck_fraction": sunfleck,
        "sky_fraction": sky,
        "shadow_blue_ratio": shadow_blue,
        "highlight_blue_ratio": highlight_blue,
        "clipped_fraction": float(np.mean((rgb8 >= 250).any(axis=-1))),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--json", help="write the results to this file as well as stdout")
    args = ap.parse_args()

    rows = [measure(p) for p in args.images]
    keys = ["log_avg_luminance", "stops_p01_p99", "sunfleck_fraction", "sky_fraction",
            "shadow_blue_ratio", "highlight_blue_ratio", "clipped_fraction"]
    print("file".ljust(40) + "".join(k[:12].rjust(13) for k in keys))
    for r in rows:
        print(r["file"].split("/")[-1][:39].ljust(40) + "".join(f"{r[k]:13.4f}" for k in keys))
    if args.json:
        with open(args.json, "w") as f:
            json.dump(rows, f, indent=2)
            f.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
