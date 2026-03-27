#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 08:43:53 2026

@author: aras
"""
import argparse
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

    # Call API if file is not already in the data folder
    filepath = "./data/helsingør.graphml"
    bbox = 12.6281, 56.0055, 12.5395, 56.0506
    if os.path.exists(filepath):
        G = ox.io.load_graphml(filepath)
    else:
        G = ox.graph.graph_from_bbox(bbox, simplify=True)
        ox.io.save_graphml(G, filepath)


    # Load the graph and edges
    G = ox.project_graph(G)
    
    filepath_pan = "./data/helsingør.h5"

    if(os.path.exists(filepath_pan)):
        n, e = ox.graph_to_gdfs(G)
        e = e.reset_index()
        network = pdna.Network.from_hdf5(filepath_pan)
    else:
        n, e = ox.graph_to_gdfs(G)
        e = e.reset_index()
        network = pdna.Network(n.geometry.x, n.geometry.y, e["u"], e["v"], e[["length"]])

        network.save_hdf5(filepath_pan)


    # Tags with subtags fetched from the Overpass API once
    tags = {
        "amenity": ["clinic", "pharmacy", "school"],
        "shop": ["supermarket", "convenience"]
    }

    all_pois = ox.features_from_bbox(bbox, tags=tags).to_crs(n.crs)
    all_pois["geometry"] = all_pois.centroid

    reducedpois = pd.DataFrame(all_pois, columns=["geometry", "amenity", "education", "shop", "healthcare"])
    reducedpois = reducedpois.droplevel("element")
    reducededges = pd.DataFrame(e, columns=["u", "v"])

    # Takes all nodes connected by edges and assigns an integer ID from 0 to (n-1)
    featherIDtoOSMID = {}
    counter = 0
    for index, row in reducededges.iterrows():
        node1 = row['u']
        node2 = row['v']

        if node1 not in featherIDtoOSMID:
            featherIDtoOSMID[node1] = counter
            counter += 1

        if node2 not in featherIDtoOSMID:
            featherIDtoOSMID[node2] = counter
            counter += 1

   

    # Converts the old edges dataframe into a dataframe with the new node IDs
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
        "shop":     all_pois[all_pois["shop"].isin(["supermarket", "convenience"])],
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

Convert()