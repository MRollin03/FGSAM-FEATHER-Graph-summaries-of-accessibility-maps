#!/bin/bash

#
# This script runs a long JSON of cites to do Feather analysis 
# All of the inputs/argemnts for each city can be added to the 
# ./batchdata.json file and settings to the settings.json
#


# read each item in the JSON array to an item in the Bash array
readarray -t settings < <(jq --compact-output '.[]' data.json)
readarray -t locations < <(jq --compact-output '.[]' data.json)

item=${locations[0]}
  evalpoints=$(jq --raw-output '.eval_points' <<< "$item")
  thetamax=$(jq --raw-output '.thetamax' <<< "$item")
  order=$(jq --raw-output '.order' <<< "$item")
  output=$(jq --raw-output '.output' <<< "$item")

  echo "-------------------------------------------"
  echo "Settings for batch running Feather Analysis"
  echo "-------------------------------------------"
  echo "evalpoints: $evalpoints"
  echo "thetamax: $thetamax"
  echo "order: $order"
  echo "-------------------------------------------"
  echo ""

# iterate through the Bash array
for item in "${locations[@]:1}"; do

  # If name/file already exist in projects folder skip
  name=$(jq --raw-output '.name' <<< "$item")
  DIRECTORY="projects/$name"
  if [! -d "$DIRECTORY" ]; then
    echo "$DIRECTORY does exist. Skipping OSM to feather compatibility conversion"
    bbox=$(jq --raw-output '.bbox' <<< "$item")
    west=$(jq --raw-output '.bbox.west' <<< "$item")
    south=$(jq --raw-output '.bbox.south' <<< "$item")
    east=$(jq --raw-output '.bbox.east' <<< "$item")
    north=$(jq --raw-output '.bbox.north' <<< "$item")
    echo "City name: $name"
    echo $bbox
    echo $west
    echo $south
    echo $east
    echo $north

    #Converts OSM data into feather compatible input files
    python OSM2FeatherConverter.py --type BBOX --bbox "$west" "$south" "$east" "$north" --title "$name" --output "$output" --distance 1000

  fi

  #Feeds the files into Feather to create Node embeddings
  python FEATHER/src/main.py --graph-input "$output""/""$name""/FeatherEdges.csv" --feature-input "./""$output""/""$name""/featuresteis.csv"

done
