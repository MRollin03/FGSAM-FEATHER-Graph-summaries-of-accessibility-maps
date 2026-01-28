This repository contains a research-oriented project exploring **accessibility analysis for the 15-minute city concept**, with a focus on comparing traditional accessibility tools with a FEATHER based approch.

## Problem Statement

The **15-minute city** is an urban planning concept introduced by Carlos Moreno in 2016. It describes a city where residents can access all essential daily services—such as work, education, healthcare, shopping, and social activities—within a **15-minute walking distance** from their home.

The concept emphasizes:

* Improved **accessibility**
* Reduced **dependence on cars**
* Increased **social equity**, regardless of mobility or socioeconomic status

In this project, accessibility is defined as the **ability to reach essential services and amenities within a 15-minute threshold**, which serves as a continuous value rather than a strict cutoff.

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
