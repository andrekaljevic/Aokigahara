#!/usr/bin/env bash
# Migrate this repository's binary assets from plain Git objects into Git LFS.
#
# Run this from a machine that can reach lfs.github.com. The session that first
# published the repository could not: its egress gateway refused CONNECT to that
# host, so the assets were committed directly to keep them from being lost.
#
# This rewrites history for the listed paths. Coordinate with anyone who has
# cloned the repository before running it, then force-push.
set -euo pipefail
cd "$(dirname "$0")/.."

command -v git-lfs >/dev/null || { echo "git-lfs is not installed"; exit 1; }

INCLUDE='*.glb,*.gltf,*.fbx,*.blend,*.obj,*.exr,*.hdr,*.tif,*.tiff,*.f32,*.npz,*.zip,*.7z,*.bin,*.pdf,viewer/assets/materials/*.jpg,viewer/assets/materials_v2/*.jpg,viewer/assets/materials_v2/*.png,renders/**/*.png,renders/**/*.jpg,docs/handover/*.png'

echo "Installing LFS filters..."
git lfs install --local

echo "Restoring the intended LFS ruleset..."
cp .gitattributes.lfs .gitattributes

echo "Rewriting history for: $INCLUDE"
git lfs migrate import --include="$INCLUDE" --everything

git add .gitattributes
git commit -m "Move binary assets into Git LFS" || true

cat <<'MSG'

Done locally. Now:
    git lfs push --all origin
    git push --force-with-lease origin --all

Verify afterwards with:
    git lfs ls-files | wc -l
    python3 tools/verify_manifest.py
MSG
