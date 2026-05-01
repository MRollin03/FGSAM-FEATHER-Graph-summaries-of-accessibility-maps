#!/bin/bash

# Læs alle elementer fra data.json ind i et array
readarray -t locations < <(jq --compact-output '.[]' data.json)
echo "Loaded locations: ${#locations[@]}"

# Hent globale settings fra det første element (index 0)
item=${locations[0]}
output=$(jq --raw-output '.output' <<< "$item")

if [ "$output" == "null" ]; then
    echo "Fejl: Output-sti ikke fundet i JSON."
    exit 1
fi

echo "-------------------------------------------"
echo "Running Grapher Turbo batch"
echo "-------------------------------------------"

# Iterer gennem lokationer (starter fra index 1)
for item in "${locations[@]:1}"; do
    name=$(jq --raw-output '.name' <<< "$item")
    DIRECTORY="${output}/${name}"

    # Tjek om data findes
    if [ ! -d "$DIRECTORY" ]; then
        echo "Skipping $name: Directory does not exist."
        continue
    fi

    echo "Processing: $name"

    python grapher_turbo.py --input "$DIRECTORY" --name "$name"
done