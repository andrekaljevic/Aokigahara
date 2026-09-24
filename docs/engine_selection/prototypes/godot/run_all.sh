#!/bin/bash
# Renders the lighting-probe frames sequentially on lavapipe (software Vulkan) under Xvfb.
cd "$(dirname "$0")"
G=$PWD/bin/Godot_v4.7.2-stable_linux.x86_64
for spec in "sdfgi 30" "nosdfgi 24" "canopy 24" "$@"; do
  set -- $spec; mode=$1; frames=$2
  [ -z "$mode" ] && continue
  s=$(date +%s.%N)
  timeout 900 xvfb-run -a -s "-screen 0 1280x800x24" $G --path proj --rendering-driver vulkan \
    --rendering-method forward_plus --resolution 1280x800 -- --mode=$mode --frames=$frames > logs/$mode.log 2>&1
  echo "$mode exit=$? wall_s=$(echo "$(date +%s.%N)-$s" | bc)" | tee -a logs/wall.txt
done
echo ALLDONE >> logs/wall.txt
