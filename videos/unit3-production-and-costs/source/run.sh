#!/bin/bash
# usage: run.sh <file> <Scene> [q]   (q = quick 480p preview)
cd /tmp/claude-0/proj
if [ "$3" = "q" ]; then /tmp/claude-0/mv/bin/manim -r 854,480 --fps 15 --disable_caching --media_dir media_$2 "$1.py" "$2" 2>&1 | tail -4
else /tmp/claude-0/mv/bin/manim -r 1920,1080 --fps 30 --disable_caching --media_dir media_$2 "$1.py" "$2" 2>&1 | tail -4; fi
