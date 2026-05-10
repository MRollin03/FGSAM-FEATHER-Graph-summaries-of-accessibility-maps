#!/bin/bash

# Læs alle elementer fra data.json ind i et array
readarray -t locations < <(jq --compact-output '.[]' data.json)

# Hent globale settings fra det første element (index 0)
item=${locations[0]}
evalpoints=$(jq --raw-output '.evalpoints' <<< "$item")
thetamax=$(jq --raw-output '.thetamax' <<< "$item")
order=$(jq --raw-output '.order' <<< "$item")
output=$(jq --raw-output '.output' <<< "$item")

if [ "$output" == "null" ]; then
    echo "Fejl: Output-sti ikke fundet i JSON."
    exit 1
fi

echo "-------------------------------------------"
echo "Settings for batch running Feather Analysis"
echo "-------------------------------------------"
echo "evalpoints: $evalpoints | thetamax: $thetamax | order: $order"
echo "-------------------------------------------"

# Iterer gennem lokationer (starter fra index 1)
for item in "${locations[@]:1}"; do
    name=$(jq --raw-output '.name' <<< "$item")
    DIRECTORY="projects/$name"

    # Tjek om projektet allerede findes
    if [ -d "$DIRECTORY" ]; then
        echo "Skipping $name: Directory already exists."
        continue
    fi

    echo "Processing city: $name"

    # Checking if its BBOX or PLACE
    bbox=$(jq --raw-output '.bbox' <<< "$item")
    if [[ "$bbox" != "null" ]]; then

      # Hent koordinater
      west=$(jq --raw-output '.bbox.west' <<< "$item")
      south=$(jq --raw-output '.bbox.south' <<< "$item")
      east=$(jq --raw-output '.bbox.east' <<< "$item")
      north=$(jq --raw-output '.bbox.north' <<< "$item")

      # 1. Konverter OSM data
      python OSM2FeatherConverter.py --type BBOX --bbox "$west" "$south" "$east" "$north" \
          --title "$name" --output "$output" 
      else

      python OSM2FeatherConverter.py --type PLACE --place "$name" --title "$name" --output "$output"

    fi

    #python GraphMaker.py --input "$name" --order  $order 

done
