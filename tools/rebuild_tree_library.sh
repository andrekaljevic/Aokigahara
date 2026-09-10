#!/bin/sh
# Rebuild viewer/assets/tree-library-v2.glb from construction_code_v2/generate_trees_v2.py.
#
# Two steps, because the generator embeds each texture by reading the file in work/tex/ verbatim,
# and work/tex/ is scratch that the repository does not carry. Its GEOMETRY is faithful - running
# the generator unmodified reproduces all 330 of the shipped library's accessor buffer views
# byte-for-byte - but rebuilding from textures re-extracted at source resolution inflates the file
# from 12.5 MB to 16.0 MB for no visual gain. So step two grafts the shipped image payload back on.
#
# With the generator unmodified, the result is byte-identical to the library the original session
# shipped (sha256 1a237cf7d2e801fcd2dabf2ded66d9eff29578ceeed73466ec442b53b87d244a). That is the
# check to run first if you are about to change the generator: if it does not reproduce, something
# other than your edit is different.
#
#   sh tools/rebuild_tree_library.sh [reference.glb]
#
# reference.glb defaults to the current viewer/assets/tree-library-v2.glb, so run it on a clean
# checkout, or pass an explicit reference. Verify the result with:
#   python3 tools/compare_glb.py viewer/assets/tree-library-v2.glb <reference.glb>
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT="$ROOT/viewer/assets/tree-library-v2.glb"
REF=${1:-"$ROOT/.tree-library-v2.reference.glb"}
TMP="$ROOT/work/tree-library-v2.generated.glb"
mkdir -p "$ROOT/work"

if [ ! -f "$REF" ]; then
  REF="$TMP.reference"
  cp "$OUT" "$REF"
  echo "using the current library as the texture reference: $REF"
fi

python3 "$ROOT/construction_code_v2/generate_trees_v2.py"
mv "$OUT" "$TMP"
python3 "$ROOT/tools/graft_textures.py" "$TMP" "$REF" "$OUT" \
        --manifest "$ROOT/viewer/assets/tree-library-v2.json"
rm -f "$TMP"
echo
echo "done. Compare against the reference with:"
echo "  python3 tools/compare_glb.py $OUT $REF"
