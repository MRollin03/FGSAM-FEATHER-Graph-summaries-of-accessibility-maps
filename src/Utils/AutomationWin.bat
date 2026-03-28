@echo off

set projectName=Odense
set baseDir=projects
REM Select either BBOX or PLACE
set MODE=PLACE

REM bounding box
set west=12.27259
set south=56.10713
set east=12.34640
set north=56.13288

REM Remember to replace the spaces with underscores ( _ )
set location=Odense_Municipality

echo Starting Conversion of places!
REM Kør konvertering baseret på MODE
IF "%MODE%"=="PLACE" (
    python OSM2FeatherConverter.py --type %MODE% --place %location% --title %projectName% --output %baseDir%
) ELSE (
    python OSM2FeatherConverter.py --type %MODE% --bbox %west% %south% %east% %north% --title %projectName% --output %baseDir%
)

REM Fortsæt kun hvis de næste skridt lykkes
python FEATHER/src/main.py --graph-input "%baseDir%/%projectName%/FeatherEdges.csv" --feature-input "%baseDir%/%projectName%/featuresteis.csv" --output "%baseDir%/%projectName%/FeatherResult.csv"

python NodeEmbedding.py --title %projectName% --input "%baseDir%/%projectName%/FeatherResult.csv" --output "%baseDir%/%projectName%"

echo Done converting
