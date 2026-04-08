#!/bin/bash

projectName="Gilleleje"
baseDir="projects"
MODE=BBOX # Select either [PLACE, BBOX]

# Coordinates or Location
west=12.27259
south=56.10713
east=12.34640
north=56.13288

# Remember to replace the spaces with underscores ( _ )
location="Odense_Municipality"

echo "Starting Conversion of places!"

# Kør konvertering baseret på MODE
if [ "$MODE" = PLACE ]; then
    python OSM2FeatherConverter.py --type "$MODE" --place "$location" --title "$projectName" --output "$baseDir"
else
    python OSM2FeatherConverter.py --type BBOX --bbox "$west" "$south" "$east" "$north" --title "$projectName" --output "$baseDir"
fi

# Fortsæt kun hvis de næste skridt lykkes
python FEATHER/src/main.py --graph-input "$baseDir""/""$projectName""/FeatherEdges.csv" --feature-input "./""$baseDir""/""$projectName""/featuresteis.csv" --output "./""$baseDir""/""$projectName""/FeatherResult.csv" --eval-points 5 &&

python NodeEmbedding.py --title "$projectName" --input "$baseDir""/""$projectName""/FeatherResult.csv" --output "./""$baseDir""/""$projectName"

echo "Done converting"
