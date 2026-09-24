#!/usr/bin/env python3
"""Dress real-terrain depth panoramas with Marble and download the resulting worlds.

Two World API calls per viewpoint:
  1. POST /marble/v1/pano:depth_to_rgb  depth panorama (EXR) + text prompt -> photographic pano
  2. POST /marble/v1/worlds:generate    that pano as an image prompt       -> Gaussian-splat world
Then the world's SPZ splats (100k / 500k / full), collider mesh, pano and metric-scale metadata
are downloaded next to a JSON record of every request, response and credit balance.

Needs WLT_API_KEY in the environment (an API key from platform.worldlabs.ai; API credit is bought
there, separately from the Marble web app). Nothing here reads or prints the key.

Costs (docs.worldlabs.ai/api/pricing, checked 23 Sep 2026): world generation from a pano 1,500
credits with marble-1.1 (about $1.20), 150 with marble-1.0-draft; the depth-to-RGB step is not
priced in the docs, so the balance is recorded before and after each call.

Usage:
    python3 tools/marble_test/marble_api.py credits
    python3 tools/marble_test/marble_api.py run --pano DIR/08LE9335_v2 --out OUT [--model marble-1.0-draft]
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.worldlabs.ai/marble/v1"

PROMPT = (
    "Aokigahara, the Sea of Trees at the northwest foot of Mount Fuji, Japan: an old-growth forest "
    "of Japanese hemlock and hinoki cypress growing straight out of a black basalt lava flow. The "
    "lava ground is lumpy and uneven, completely carpeted in thick, deep green moss, with a tangle "
    "of exposed surface roots snaking over the rock, fallen mossy logs, scattered ferns, dead "
    "needles and small twigs. Slender grey-brown trunks with lichen, a dense dark canopy with small "
    "gaps of pale sky. Soft, even overcast daylight, no direct sun, quiet and still. Photorealistic, "
    "natural colour as in a real photograph. The 360 scene is faultless."
)


def key():
    k = os.environ.get("WLT_API_KEY")
    if not k:
        sys.exit("WLT_API_KEY is not set. Add it as an environment variable in the cloud "
                 "environment's settings and start a new session.")
    return k


def call(path, method="GET", body=None):
    req = urllib.request.Request(
        f"{API}/{path}", method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"WLT-Api-Key": key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            txt = r.read().decode()
            return json.loads(txt) if txt else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path}: {e.code} {e.read().decode()[:2000]}") from e


def credits():
    return call("credits")


def wait(op, label, every=10, limit=3600):
    t0 = time.time()
    while True:
        cur = call(f"operations/{op['operation_id']}")
        if cur.get("done"):
            if cur.get("error"):
                raise RuntimeError(f"{label} failed: {json.dumps(cur['error'])}")
            print(f"  {label}: done in {time.time() - t0:.0f} s")
            return cur
        if time.time() - t0 > limit:
            raise RuntimeError(f"{label}: still running after {limit} s")
        time.sleep(every)


def fetch(url, path):
    with urllib.request.urlopen(url, timeout=600) as r, open(path, "wb") as f:
        f.write(r.read())
    return os.path.getsize(path)


def run(pano_base, out, model, prompt):
    os.makedirs(out, exist_ok=True)
    name = os.path.basename(pano_base)
    meta = json.load(open(pano_base + ".json"))
    rec = {"view": name, "viewpoint": meta, "model": model, "prompt": prompt, "steps": []}
    rec["credits_before"] = credits()

    exr = base64.b64encode(open(pano_base + "_depth.exr", "rb").read()).decode()
    op = call("pano:depth_to_rgb", "POST", {
        "depth_pano_image": {"source": "data_base64", "data_base64": exr, "extension": "exr"},
        "text_prompt": prompt,
    })
    res = wait(op, "depth to RGB")
    pano_url = res["response"]["pano_url"]
    fetch(pano_url, os.path.join(out, f"{name}_rgb_pano.jpg"))
    rec["steps"].append({"step": "depth_to_rgb", "operation": res})
    rec["credits_after_pano"] = credits()

    op = call("worlds:generate", "POST", {
        "display_name": f"Aokigahara {name}",
        "model": model,
        "permission": {"public": False},
        "tags": ["aokigahara", "depth-pano-test"],
        "world_prompt": {"type": "image", "is_pano": True, "text_prompt": prompt,
                         "image_prompt": {"source": "uri", "uri": pano_url}},
    })
    res = wait(op, "world generation")
    rec["steps"].append({"step": "worlds_generate", "operation": res})
    world_id = res["response"].get("world_id") or res["response"].get("id")
    world = call(f"worlds/{world_id}")
    rec["world"] = world
    rec["credits_after_world"] = credits()

    assets = (world.get("world") or world).get("assets") or {}
    files = {}
    for tier, url in ((assets.get("splats") or {}).get("spz_urls") or {}).items():
        files[f"spz_{tier}"] = fetch(url, os.path.join(out, f"{name}_{tier}.spz"))
    if (assets.get("mesh") or {}).get("collider_mesh_url"):
        files["collider"] = fetch(assets["mesh"]["collider_mesh_url"], os.path.join(out, f"{name}_collider.glb"))
    if (assets.get("imagery") or {}).get("pano_url"):
        files["world_pano"] = fetch(assets["imagery"]["pano_url"], os.path.join(out, f"{name}_world_pano.jpg"))
    rec["files"] = files
    with open(os.path.join(out, f"{name}_record.json"), "w") as f:
        json.dump(rec, f, indent=2)
        f.write("\n")
    print(json.dumps({"world_id": world_id, "files": files,
                      "credits": [rec["credits_before"], rec["credits_after_pano"], rec["credits_after_world"]]}, indent=2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("credits")
    r = sub.add_parser("run")
    r.add_argument("--pano", required=True, help="path prefix of a depth_pano.py output, without suffix")
    r.add_argument("--out", required=True)
    r.add_argument("--model", default="marble-1.1", choices=["marble-1.0-draft", "marble-1.0", "marble-1.1", "marble-1.1-plus"])
    r.add_argument("--prompt", default=PROMPT)
    a = ap.parse_args()
    if a.cmd == "credits":
        print(json.dumps(credits(), indent=2))
    else:
        run(a.pano, a.out, a.model, a.prompt)


if __name__ == "__main__":
    main()
