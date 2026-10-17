#!/bin/bash

if ! command -v conda &> /dev/null; then
    echo "Conda is not installed."
    echo "Please install Miniconda first:"
    echo "https://docs.conda.io/projects/miniconda/en/latest/"
    exit 1
fi

eval "$(conda shell.bash hook)"

conda activate backend

hand_signs=(
	"monkey"
	"dragon"
	"rat"
	"bird"
	"snake"
	"ox"
	"dog"
	"horse"
	"tiger"
	"boar"
	"ram"
	"hare"
	)

for item in "${hand_signs[@]}"; do
  echo "$item"
  python extract_hand_landmark.py ../shared/models/hand_landmarker.task ~/Videos/$item.mp4 -o ~/Videos/$item
done
