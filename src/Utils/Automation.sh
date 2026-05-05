#!/bin/bash

projectName="Copenhagen"
baseDir="projects"
MODE=Place # Select either [PLACE, BBOX, MULTI_PLACE]

# Coordinates or Location
west=12.24358
south=55.91420
east=12.34091
north=55.95679


# Remember to replace the spaces with underscores ( _ )
location="Odense_Municipality"
locations="Copenhagen Municipality, Denmark"     "Frederiksberg Municipality, Denmark"     "Tårnby Municipality, Denmark"     "Dragør Municipality, Denmark"     "Rødovre Municipality, Denmark"     "Hvidovre Municipality, Denmark"     "Gladsaxe Municipality, Denmark"     "Gentofte Municipality, Denmark"     "Glostrup Municipality, Denmark"     "Albertslund Municipality, Denmark"     "Høje-Taastrup Municipality, Denmark"     "Ishøj Municipality, Denmark"     "Ballerup Municipality, Denmark"     "Herlev Municipality, Denmark"     "Lyngby-Taarbæk Municipality, Denmark"

#Feather argument/values
order=10
thetamax=10
evalpoints=50

pandana_distance=5000

echo "Starting Conversion of places!"

# Kør konvertering baseret på MODE
if [ "$MODE" = PLACE ]; then
    python OSM2FeatherConverter.py --type "$MODE" --place "$location" --title "$projectName" --output "$baseDir" --distance $pandana_distance
else
    python OSM2FeatherConverter.py --type BBOX --bbox "$west" "$south" "$east" "$north" --title "$projectName" --output "$baseDir" --distance $pandana_distance 
fi

# Fortsæt kun hvis de næste skridt lykkes
python FEATHER/src/main.py --graph-input "$baseDir""/""$projectName""/FeatherEdges.csv" --feature-input "./""$baseDir""/""$projectName""/featuresteis.csv" --output "./""$baseDir""/""$projectName""/FeatherResult.csv" --eval-points $evalpoints --order $order --theta-max $thetamax  &&

python GraphMaker.py --input "$projectName" --order  $order 



