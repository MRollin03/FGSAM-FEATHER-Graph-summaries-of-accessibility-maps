#!/bin/bash

projectName="test"
baseDir="projects"
MODE=BBOX # Select either [PLACE, BBOX, MULTI_PLACE]

# Coordinates or Location
west=12.24358
south=55.91420
east=12.34091
north=55.95679


# Remember to replace the spaces with underscores ( _ )
location="Odense_Municipality"
locations=["Copenhagen Municipality, Denmark" ,\
   "Frederiksberg Municipality, Denmark" ,\
    "Tårnby Municipality, Denmark" ,\
    "Dragør Municipality, Denmark" ,\
    "Rødovre Municipality, Denmark" ,\
    "Hvidovre Municipality, Denmark",\
    "Gladsaxe Municipality, Denmark",\
    "Gentofte Municipality, Denmark",\
    "Glostrup Municipality, Denmark",\
    "Albertslund Municipality, Denmark",\
    "Høje-Taastrup Municipality, Denmark",\
    "Ishøj Municipality, Denmark",\
    "Ballerup Municipality, Denmark",\
    "Herlev Municipality, Denmark",\
    "Lyngby-Taarbæk Municipality, Denmark"]

# Feather argument/values
order=10
thetamax=2.5
evalpoints=25

# s < 0 && n <= orders
plotorders="1,2,3,4,5,6,7,8"



# Calculate with pandana
pananaFeature=False
pandana_distance=100000


echo "Starting Conversion of places!"

# Run Conversion based on MODE
if [ "$MODE" = "PLACE" ]; then
    python OSM2FeatherConverter.py \
        --type "$MODE" \
        --place "$location" \
        --title "$projectName" \
        --output "$baseDir" \
        --distance "$pandana_distance" \
        --pandana "$pandana_feature"\
        --order "$order"\
        --plotorders "$plotorders"

elif [ "$MODE" = "BBOX" ]; then
    python OSM2FeatherConverter.py \
        --type BBOX \
        --bbox "$west" "$south" "$east" "$north" \
        --title "$projectName" \
        --output "$baseDir" \
        --distance "$pandana_distance" \
        --pandana "$pandana_feature"\
        --order "$order"\
        --plotorders "$plotorders"

else
    python OSM2FeatherConverter.py \
        --type MULTI_PLACE \
        --places "$places" \
        --title "$projectName" \
        --output "$baseDir" \
        --distance "$pandana_distance" \
        --pandana "$pandana_feature"\
        --order "$order"\
        --plotorders "$plotorders"
fi

echo "Conversion Ended"


