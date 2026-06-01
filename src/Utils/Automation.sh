#!/bin/bash

projectName="testtest"
baseDir="projects"
MODE=BBOX # Select either [PLACE, BBOX, MULTI_PLACE]

# Coordinates or Location
west=12.34563
south=55.93977
east=12.35129
north=55.94290


# Remember to replace the spaces with underscores ( _ )
location="Copenhagen Municipality, Denmark"
locations=(
    "Copenhagen Municipality, Denmark"
    "Frederiksberg Municipality, Denmark"
    "Tårnby Municipality, Denmark"
    "Dragør Municipality, Denmark"
    "Rødovre Municipality, Denmark"
    "Hvidovre Municipality, Denmark"
    "Gladsaxe Municipality, Denmark"
    "Gentofte Municipality, Denmark"
    "Glostrup Municipality, Denmark"
    "Albertslund Municipality, Denmark"
    "Høje-Taastrup Municipality, Denmark"
    "Ishøj Municipality, Denmark"
    "Ballerup Municipality, Denmark"
    "Herlev Municipality, Denmark"
    "Lyngby-Taarbæk Municipality, Denmark")

# Feather argument/values
order=10
thetamax=2.5
evalpoints=25

# s < 0 && n <= orders
plotorders="9,10"



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
        --type "$MODE" \
        --bbox "$west" "$south" "$east" "$north" \
        --title "$projectName" \
        --output "$baseDir" \
        --distance "$pandana_distance" \
        --pandana "$pandana_feature"\
        --order "$order"\
        --plotorders "$plotorders"

else
    echo "DEBUG places:"
    printf '%s\n' "${locations[@]}"
    python OSM2FeatherConverter.py \
        --type "$MODE" \
        --places "${locations[@]}" \
        --title "$projectName" \
        --output "$baseDir" \
        --distance "$pandana_distance" \
        --pandana "$pandanaFeature" \
        --order "$order" \
        --plotorders "$plotorders"
fi

echo "Conversion Ended"


