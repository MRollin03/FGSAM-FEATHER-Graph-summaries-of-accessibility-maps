@echo off

set projectName=...
set baseDir=projects
:: Select either BBOX or PLACE
set MODE=...

:: bounding box
set west=12.27259
set south=56.10713
set east=12.34640
set north=56.13288

:: Remember to replace the spaces with underscores ( _ )
set location=...

echo Starting Conversion of places!
:: Kør konvertering baseret på MODE
if "%MODE%"=="PLACE" (
    python OSM2FeatherConverter.py --type %MODE% --place %location% --title %projectName% --output %baseDir%
) else (
    python OSM2FeatherConverter.py --type %MODE% --bbox %west% %south% %east% %north% --title %projectName% --output %baseDir%
)

:: Fortsæt kun hvis de næste skridt lykkes
python FEATHER/src/main.py --graph-input "%baseDir%/%projectName%/FeatherEdges.csv" --feature-input "%baseDir%/%projectName%/featuresteis.csv" --output "%baseDir%/%projectName%/FeatherResult.csv"

python NodeEmbedding.py --title %projectName% --input "%baseDir%/%projectName%/FeatherResult.csv" --output "%baseDir%/%projectName%"

echo Done converting
