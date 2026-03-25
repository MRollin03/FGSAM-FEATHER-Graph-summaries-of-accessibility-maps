#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 08:43:53 2026

@author: aras
"""

import pandas as pd
from pathlib import Path
import osmnx as ox
import os
import pandana as pdna

ox.settings.use_cache = True
ox.settings.log_console = True





def Convert():
    '''
    This function takes in a bbox (a set of coordinates to indicate an area on a map)
    and converts all of its features into csv files that are appropriate for the
    Feather algorithm. ref = https://github.com/benedekrozemberczki/FEATHER
    '''

    # --- Configuration ---
    Path("./output").mkdir(exist_ok=True) # Output directory 
    filepath = "./data/København.graphml" # Graph File
    filepath_pan = "./data/København.h5"  # Featues Files
    
    ConvertType = "PLACE"                           # Either "BBOX" or "PLACE"
    bbox = 12.6281, 56.0055, 12.5395, 56.0506       # Used if ConverType is "BBOx"
    placenames = ["Copenhagen Municipality, Denmark",
                  "Frederiksberg Municipality, Denmark",
                  "Tårnby Municipality, Denmark",
                  "Dragør Municipality, Denmark",
                  "Rødovre Municipality, Denmark",
                  "Hvidovre Municipality, Denmark",
                  "Gladsaxe Municipality, Denmark",
                  "Gentofte Municipality, Denmark"
                  ]   # Used if ConvertType is "PLACE"

    tags = {
        "amenity": ["pharmacy", "school"],
        "shop": ["supermarket", "convenience"]
    }

    # --- Load or fetch graph ---
    if os.path.exists(filepath):
        G = ox.io.load_graphml(filepath)
    else:
        if ConvertType == "BBOX":
            G = ox.graph.graph_from_bbox(bbox, simplify=True)
        else:
            G = ox.graph.graph_from_place(placenames, simplify=True)
        ox.io.save_graphml(G, filepath)

    G = ox.project_graph(G)

    # --- Load or build pandana network ---
    n, e = ox.graph_to_gdfs(G)
    e = e.reset_index()

    if os.path.exists(filepath_pan):
        network = pdna.Network.from_hdf5(filepath_pan)
    else:
        network = pdna.Network(
            n.geometry.x, n.geometry.y,
            e["u"], e["v"], e[["length"]]
        )
        network.save_hdf5(filepath_pan)

    # --- Fetch POIs once and pass them around ---
    if ConvertType == "BBOX":
        all_pois = ox.features_from_bbox(bbox, tags=tags).to_crs(n.crs)
    else:
        all_pois = ox.features_from_place(placenames, tags=tags).to_crs(n.crs)
    all_pois["geometry"] = all_pois.centroid

    # --- Build Feather ID mapping (vectorized) ---
    reducededges = pd.DataFrame(e, columns=["u", "v"])
    unique_nodes = pd.unique(reducededges[["u", "v"]].values.ravel())
    featherIDtoOSMID = {osm_id: i for i, osm_id in enumerate(unique_nodes)}

    # --- Write outputs ---
    OsmEdgesToFeather(reducededges, featherIDtoOSMID)
    ComputeFeatures(network, n, featherIDtoOSMID, all_pois)


def OsmEdgesToFeather(ogEdges, featherIDtoOSMID):
    '''
    Converts OSM node IDs in the edge list to sequential Feather IDs
    and writes the result to ./output/FeatherEdges.csv.
    '''

    if not featherIDtoOSMID:
        raise ValueError("featherIDtoOSMID is empty")

    if ogEdges.empty:
        raise ValueError("Input edges are empty")

    convertedEdges = ogEdges[["u", "v"]].replace(featherIDtoOSMID)
    convertedEdges.to_csv("./output/FeatherEdges.csv", index=False)


def ComputeFeatures(network, n, featherIDtoOSMID, all_pois):
    '''
    For each POI category, computes the nearest POI distance for every network
    node using pandana, then writes a feature CSV for the Feather algorithm.
    Also annotates n["pois"] with a count of how many category POIs are within
    the threshold distance.
    '''

    categories = {
        "shops":     all_pois[all_pois["shop"].isin(["supermarket", "convenience"])],
        "health":    all_pois[all_pois["amenity"].isin(["pharmacy"])],
        "education": all_pois[all_pois["amenity"] == "school"],
    }

    distance = 2000   # max search distance (metres)
    dist = 500        # threshold for counting a POI as "accessible"
    n["pois"] = 0

    frames = []

    for cat, data in categories.items():
        if data.empty:
            continue

        network.set_pois(
            category=cat,
            maxdist=distance,
            maxitems=1000,
            x_col=data.geometry.x,
            y_col=data.geometry.y,
        )

        nearest_pois = network.nearest_pois(
            distance=distance,
            category=cat,
            num_pois=1,
        )
        nearest_pois.columns = [cat]

        # Count nodes that have this category's nearest POI within threshold
        n["pois"] += (nearest_pois[cat] <= dist).astype(int)

        frames.append(nearest_pois)

    if not frames:
        raise RuntimeError("No POI categories had any data — feature CSV not written.")

    featurez = pd.concat(frames, axis=1, sort=False)
    featurez.index = featurez.index.map(featherIDtoOSMID)
    featurez.sort_index(inplace=True)
    featurez.index.name = None
    featurez.to_csv("./output/featuresteis.csv", index=False)

# ---------------------------------------------------------------------------
Convert();