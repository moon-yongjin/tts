import shutil
import os
from pathlib import Path

downloads = Path("/Users/a12/Downloads")
sfx_lib = Path("/Users/a12/projects/tts/core_v2/Library/sfx")

mapping = {
    "l3hrja-deer-baby-calling-for-mama-233035.mp3": "deer_scream_distress.mp3",
    "freesound_community-bear-trap-103800.mp3": "metal_trap_snap.mp3",
    "the-vampires-monster-girl-monster-crying-sobbing-woman-386642.mp3": "old_woman_wailing.mp3",
    "freesound_community-evil-laugh-89423.mp3": "villain_laugh_mean.mp3",
    "freesound_community-digging-dirt-cu-variations-06-24481.mp3": "dirt_digging_roots.mp3"
}

for src_name, dest_name in mapping.items():
    src_path = downloads / src_name
    dest_path = sfx_lib / dest_name
    if src_path.exists():
        print(f"Moving {src_name} to {dest_name}...")
        shutil.move(str(src_path), str(dest_path))
    else:
        print(f"⚠️ Source file not found: {src_name}")
