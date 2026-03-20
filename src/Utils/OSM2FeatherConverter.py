#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 08:43:53 2026

@author: aras
"""

import pandas as pd
import numpy as np
import warnings
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
import osmnx as ox
import os
import timeit
import pyogrio
import networkx as nx
import pandana as pdna

ox.settings.use_cache = True
ox.settings.log_console = True


# In[2]:

def Convertbbox():
    '''
    This function takes in a bbox (a set of coordinates to indicate an area on a map)
    and converts all of its features into csv files that are appropriate for the
    Feather algorithm. ref = https://github.com/benedekrozemberczki/FEATHER
    '''

    # Call API if file is not already in the data folder
    filepath = "./data/silkbronx_network.graphml"
    bbox = 9.48446, 56.15291, 9.62522, 56.20804
    if os.path.exists(filepath):
        G = ox.io.load_graphml(filepath)
    else:
        G = ox.graph.graph_from_bbox(bbox, simplify=True)
        ox.io.save_graphml(G, filepath)


    # Load the graph and edges
    G = ox.project_graph(G)
    
    filepath_pan = "./data/silkbronx_network.h5"

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
    
    alt(bbox, network, n, featherIDtoOSMID)

    # Generates features into a dataframe with the necessary data for Feather
    #FeatherFeatures(G, all_pois, featherIDtoOSMID)


def FeatherFeatures(G, pois, featherIDtoOSMID):
    '''
    For each POI, finds the nearest graph node and records whether that node
    has an amenity, education facility, shop, or healthcare facility nearby.
    For nodes with no nearby POI, finds the closest POI node by shortest path.
    Writes the result to ./output/FeatherFeatures.csv.
    '''

    convertedPois = pd.DataFrame(columns=['id', 'amenity', 'education', 'shop', 'healthcare'])

    for index, row in pois.iterrows():
        nearest_node = ox.nearest_nodes(G, row['geometry'].x, row['geometry'].y)

        # FIX 4: Both branches previously returned 0 — now correctly return 1 if the field is present
        nodeamenity    = 1 if type(row.get('amenity'))    is str else 0
        nodeeducation  = 1 if type(row.get('education'))  is str else 0
        nodeshop       = 1 if type(row.get('shop'))       is str else 0
        nodehealthcare = 1 if type(row.get('healthcare')) is str else 0

        existing = convertedPois.loc[nearest_node] if nearest_node in convertedPois.index else [featherIDtoOSMID.get(nearest_node), 0, 0, 0, 0]
        convertedPois.loc[nearest_node] = [
            featherIDtoOSMID.get(nearest_node),
            max(existing[1], nodeamenity),
            max(existing[2], nodeeducation),
            max(existing[3], nodeshop),
            max(existing[4], nodehealthcare),
        ]

    for osmid, feather_id in featherIDtoOSMID.items():
        if osmid not in convertedPois.index:
            convertedPois.loc[osmid] = [feather_id, 0, 0, 0, 0]


    convertedPois = convertedPois.sort_values('id')
    convertedPois = convertedPois.drop("id", axis=1)
    convertedPois.to_csv("./output/FeatherFeatures.csv", index=False)


def OsmEdgesToFeather(ogEdges, featherIDtoOSMID):

    if not bool(featherIDtoOSMID):
        raise Exception("FeatherID2OSMID is empty")

    if ogEdges.empty:
        raise Exception("Input Edges are empty")

    convertedEdges = pd.DataFrame(columns=['u', 'v'])
    for index, row in ogEdges.iterrows():
        node1 = featherIDtoOSMID.get(row['u'])
        node2 = featherIDtoOSMID.get(row['v'])

        if node1 is None or node2 is None:
            raise Exception("One or more nodes with OSMID exists without a FeatherID")

        convertedEdges.loc[index] = [node1, node2]

    convertedEdges.to_csv("./output/FeatherEdges.csv", index=False)

    
def alt(bbox, network, n, featherIDtoOSMID):
    # These are tags with subtags or something don't know the terms
    # Made this so we only have to get the features from the overpass API once!
    tags = {
        "amenity": ["clinic", "pharmacy", "school"],
        "shop": ["supermarket", "convenience"]
    }
    all_pois = ox.features_from_bbox(bbox, tags=tags).to_crs(n.crs)
    all_pois["geometry"] = all_pois.centroid
    
    # these are Filters for filtering the specified amenities
    # Think of these as the induvidual layers
    categories = {
        #if you add a filter layer remember to add it in the sub catogory in the for two for-loops down
        "shops": all_pois[all_pois["shop"].isin(["supermarket", "convenience"])],
        "health": all_pois[all_pois["amenity"].isin(["clinic", "pharmacy"])],
        "education": all_pois[all_pois["amenity"] == "school"],
    }
    
    ### search Variables
    distance = 2000
    dist = 500
    n["pois"] = 0
    
    counta = 0
    # Goes Through the Categories  and creates the POI for the category so that we can aggregate and plot them
    for cat, data in categories.items():
        if data.empty:
            continue
            
        network.set_pois(
            category=cat,
            maxdist=2000,
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
        if counta == 0:
            featurez = pd.DataFrame(nearest_pois, columns=[cat])
        else: 
            featurez = pd.concat([featurez, nearest_pois] ,axis=1, sort=False)
        counta += 1
        n["pois"] = n["pois"] + (nearest_pois <= dist).sum(axis=1)
        
        


    featurez.index = featurez.index.map(featherIDtoOSMID)
    featurez.sort_index(inplace=True)
    featurez.index.name = None 
    featurez.to_csv('./output/featuresteis.csv', index=False)
            

# In[3]:

Convertbbox()