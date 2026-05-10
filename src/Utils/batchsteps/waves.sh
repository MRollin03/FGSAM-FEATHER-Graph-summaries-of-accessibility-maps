#!/bin/bash

readarray -t locations < <(jq --compact-output '.[]' data.json)

item=${locations[0]}
output=$(jq --raw-output '.output' <<< "$item")

echo "Loaded locations: ${#locations[@]}"

echo "Running grapher turbo batch..."

for item in "${locations[@]:1}"; do
    name=$(jq --raw-output '.name' <<< "$item")
    DIRECTORY="${output}/${name}"

    if [ ! -d "$DIRECTORY" ]; then
        echo "Skipping $name (missing folder)"
        continue
    fi

    echo "Running: $name"
    python DistributionGrapher.py "$DIRECTORY"
done

echo "Done."