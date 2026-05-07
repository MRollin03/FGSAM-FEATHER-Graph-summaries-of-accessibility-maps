This repository contains a research-oriented project exploring **accessibility analysis for the 15-minute city concept**, with a focus on comparing traditional accessibility tools with a FEATHER based approch.

## Problem Statement

The **15-minute city** is an urban planning concept introduced by Carlos Moreno in 2016. It describes a city where residents can access all essential daily services—such as work, education, healthcare, shopping, and social activities—within a **definitive walking distance** from their home.

The concept emphasises:

* Improved **accessibility**
* Reduced **dependence on cars**
* Increased **social equity**, regardless of mobility or socioeconomic status

In this project, accessibility is defined as the **ability to reach essential services and amenities within a given threshold**, which serves as a continuous value rather than a strict cutoff.

## Project Goal

The goal of this project is to explore and evaluate **new methods for urban accessibility analysis** by leveraging modern graph algorithms—specifically the **FEATHER algorithm**—and comparing them with established tools such as **GOAT (Geo Open Accessibility Tool)**.

The project aims to deliver a **FEATHER-based solution** capable of processing **OpenStreetMap (OSM)** data to produce accessibility analyses comparable to GOAT’s current capabilities.

## Research Objectives

1. **Comparative Analysis**
   Analyze FEATHER and GOAT for accessibility mapping, focusing on strengths, limitations, and practical differences through case studies or scenarios.

2. **Performance Evaluation**
   Evaluate FEATHER’s performance, robustness, and accuracy when calculating accessibility metrics within an urban environment.

3. **Methodological Extensions**
   Explore potential extensions to existing accessibility measurement methodologies that could be implemented using FEATHER.

## Methodology Overview

* Utilize **OpenStreetMap (OSM)** data as the primary spatial data source
* Apply the **FEATHER algorithm** for graph-based accessibility analysis
* Compare outputs and metrics against those produced by **GOAT**
* Document implementation details, assumptions, and limitations

## Expected Deliverables

* A FEATHER-based accessibility analysis
* Detailed documentation of the methodology and implementation
* Comparative results between FEATHER and GOAT
* Discussion of limitations and future improvements

## Literature

* Moreno, C. (2021). *Definition of the 15-minute city: What is the 15-minute city?*
  [https://www.researchgate.net/publication/362839186_Definition_of_the_15-minute_city_WHAT_IS_THE_15_MINUTE_CITY](https://www.researchgate.net/publication/362839186_Definition_of_the_15-minute_city_WHAT_IS_THE_15_MINUTE_CITY)

* OpenStreetMap Contributors. *Planet OSM.*
  [https://planet.osm.org/](https://planet.osm.org/) (Accessed: 26-01-2026)

* Rozenberczki, B., & Sarkar, R. (2020). *Characteristic Functions on Graphs: Birds of a Feather, from Statistical Descriptors to Parametric Models.*
  arXiv:2005.07959, [https://arxiv.org/pdf/2005.07959.pdf](https://arxiv.org/pdf/2005.07959.pdf) (Accessed: 26-01-2026)

## License

This project is intended for academic and research purposes. Licensing details will be added  once finalised.

## User Guide
You can run our pipeline from the Automation.sh or AutomationWin.bat files, depending on wether you use Linux/Mac or Windows respectively.
This guide will be showcasing the AutomationWin.bat file, but the process is the exact same for Automation.sh, the difference is just syntax.

You must provide the pipeline with these values:
<img width="391" height="147" alt="image" src="https://github.com/user-attachments/assets/96891f90-1fe4-44c5-b655-1055be547396" />
```
ProjectName = <the name of your project>
Basedir = the directory which act as root for the pipeline
Mode = either BBOX or PLACE depending on your type of query
```
If you use BBOX mode, then you must include the coordinates (north, east, west, south), if you use place you must fill out location with a valid OSM query such as:: ```Copenhagen_Municipality,Denmark```

### Options for OSM2FeatherConverter
The OSM2FEATHERConverter handles the osm database queries and converts the data to a FEATHER friendly format. There is provide these command lines:
```
--title   STR   Name of project
--type   STR   BBOX or PLACE 
--bbox   float  Numargs = 4  Bounding box coordinates   Only used when type is BBOX
--place   STR   Place name   Only used when type is PLACE
--solo   STR   the feature   Used if only one category is deciered   If NONE all categories will be accounted for.
--distance  int   Name of project   The distance to look for out 20 pois per cat, this is alos used as vmax for the heatmap grap
--output   STR   output direectory for the project folder
```

### Options for NodeEmbedding
```
--title   STR   Name of project
--input   STR   Path to input 
--output   STR   output direectory for the project folder
```

The options for FEATHER can be found here: https://github.com/benedekrozemberczki/FEATHER/blob/master/README.md

### Graphs




