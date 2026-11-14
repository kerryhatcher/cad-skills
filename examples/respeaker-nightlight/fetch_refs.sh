#!/bin/sh
# Download the Seeed reference models and drawings into refs/.
set -eu
cd "$(dirname "$0")"
mkdir -p refs
base=https://files.seeedstudio.com/wiki/reSpeaker_flex
for f in reSpeaker_xvf3800_flex_circular_260210.step reSpeaker_xvf3800_flex_Separate.step \
         reSpeaker_xvf3800_flex_circular_2d.dxf reSpeaker_xvf3800_flex_Separate_2d.dxf; do
  curl -fsSL -o "refs/$f" "$base/$f"
done
