#!/bin/bash

projectName="Aberdeen"

# Coordinates or Location
west=-2.2865
south=57.0486
east=-2.0428
north=57.2185

location="SOMEWHERE"

echo "Starting Convertion of places!"

# --- SELECT BETWEEN Place OR BBOX -----
# python OSM2FeatherConverter.py --type PLACE --place $location --title $projectName &&
python OSM2FeatherConverter.py --type BBOX --bbox $west $south $east $north --title $projectName &&

python FEATHER/src/main.py --graph-input $projectName/FeatherEdges.csv --feature-input $projectName/featuresteis.csv --output ./$projectName/FeatherResult.csv && 
python NodeEmbedding.py --title $projectName --input ./$projectName/FeatherResult.csv   --output ./$projectName
 

echo "Done converting"
