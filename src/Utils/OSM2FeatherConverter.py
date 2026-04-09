#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 19 08:43:53 2026

@author: aras
"""
import argparse
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import osmnx as ox
import os
import pandana as pdna

ox.settings.use_cache = True
ox.settings.log_console = True

def Convert(args):
    '''
    This function takes in a bbox (a set of coordinates to indicate an area on a map)
    and converts all of its features into csv files that are appropriate for the
    Feather algorithm. ref = https://github.com/benedekrozemberczki/FEATHER
    '''
    
    # Tags with subtags fetched from the Overpass API once
    # Accessibility amenity tags for Overpass API queries
    tags = {
        "leisure": [
            # Outdoor Activities
            "park", "playground", "bathing_place", "garden", "pitch",
            "stadium", "swimming_area", "track",
            # Physical Exercise
            "fitness_centre", "fitness_station", "sports_centre", "swimming_pool",
        ],
        "amenity": [
            # Learning
            "college", "school", "library", "kindergarten", "university", "training",
            # Eating
            "pub", "cafe", "restaurant", "fast_food", "food_court", "biergarten",
            # Cultural Activities
            "cinema", "community_centre", "theatre",
            # Services
            "fire_station", "police", "post_office", "post_box", "townhall", "toilets",
            # Healthcare
            "clinic", "dentist", "doctors", "hospital", "pharmacy", "veterinary",
            # Financial
            "atm", "bank", "payment_terminal", "payment_centre",
        ],
        "shop": [
            # Supplies
            "department_store", "general", "mall", "supermarket", "convenience",
            "bakery", "butcher", "greengrocer", "books", "stationery", "clothes",
            "shoes", "appliance", "doityourself", "furniture", "electronics", "houseware",
        ],
        "public_transport": [
            # Moving
            "platform", "station", "stop_position",
        ],
        "tourism": [
            # Cultural Activities
            "aquarium", "gallery", "museum", "zoo",
            # Outdoor Activities
            "picnic_site",
        ],
    }
    #ox.settings.overpass_url = "https://overpass.maprva.org/api/"
    graphml_path = args.output + "/" + args.title + "/" + args.title + ".graphml"
    pandana_path = args.output + "/" + args.title + "/" + args.title + ".h5"
    
    if args.title == None:
        raise ValueError("You need a Title for your project")

    if not os.path.exists(graphml_path):
        
        if args.type == "BBOX":
            G = ox.graph.graph_from_bbox(args.bbox, simplify=True)
        if args.type == "PLACE":
            G = ox.graph.graph_from_place(args.place, simplify=True)
        ox.io.save_graphml(G, graphml_path)
    else:
        G = ox.io.load_graphml(graphml_path)

    # Load the graph and edges
    G = ox.project_graph(G)

    if(os.path.exists(pandana_path)):
        n, e = ox.graph_to_gdfs(G)
        e = e.reset_index()
        network = pdna.Network.from_hdf5(pandana_path)
    else:
        n, e = ox.graph_to_gdfs(G)
        e = e.reset_index()
        network = pdna.Network(n.geometry.x, n.geometry.y, e["u"], e["v"], e[["length"]])

        network.save_hdf5(pandana_path)

    if args.type == "BBOX":
        
        all_pois = ox.features_from_bbox(args.bbox, tags).to_crs(n.crs)
        all_pois["geometry"] = all_pois.centroid
    
    if args.type == "PLACE":
        
        all_pois = ox.features_from_place(args.place, tags).to_crs(n.crs)
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
    
    nearest_pois = ComputeFeatures(network, n, featherIDtoOSMID, all_pois)
    if args.solo == None:
        fig, ax = ox.plot.plot_graph(
            G,
            node_size=0,
            edge_color="#afdffe",
            edge_linewidth=0.6,
            bgcolor="#1a1a1a",
            show=False,
            close=False,
            figsize=(36,34)
        )
    
        vmin = nearest_pois["pois"].min()
        vmax=args.distance
        nearest_pois.plot(
            ax=ax,
            column="pois",
            cmap="plasma",
            markersize=3.5,
            alpha=0.8,
            legend=True,
            legend_kwds={
                "shrink": 0.5,
                "label": f"Number of pois ≤ {vmax} m",
                "orientation": "vertical"
            },
            vmin=vmin,
            vmax=args.distance
        )
        
        plt.savefig(args.output + "/" + args.title + "/" + "all_pois")
    else:
        fig, ax = ox.plot.plot_graph(
            G,
            node_size=0,
            edge_color="#afdffe",
            edge_linewidth=0.6,
            bgcolor="#1a1a1a",
            show=False,
            close=False,
            figsize=(36,34)
        )
        vmin = nearest_pois[args.solo].min()
        vmax=args.distance
        nearest_pois.plot(
            ax=ax,
            column=args.solo,
            cmap="plasma",
            markersize=3.5,
            alpha=0.8,
            legend=True,
            legend_kwds={
                "shrink": 0.5,
                "label": f"Number of pois ≤ {vmax} m",
                "orientation": "vertical"
            },
            vmin=vmin,
            vmax=args.distance
        )
        
        plt.savefig(args.output + "/" + args.title + "/" + args.solo + "_pois")
    return exit(0)

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
    convertedEdges.to_csv("./" + args.output + "/" + args.title +  "/FeatherEdges.csv", index=False)



def ComputeFeatures(network, n, featherIDtoOSMID, all_pois):
    '''
    For each POI category, computes the nearest POI distance for every network
    node using pandana, then writes a feature CSV for the Feather algorithm.
    Also annotates n["pois"] with a count of how many category POIs are within
    the threshold distance.
    '''

    categories = {
        # --- OUTDOOR ACTIVITIES ---
        "outdoor_activities":   pd.concat([
                                    all_pois[all_pois["leisure"].isin(["park", "playground", "bathing_place", "garden", "pitch", "stadium", "swimming_area", "track"])],
                                    all_pois[all_pois["tourism"] == "picnic_site"]
                                ]).drop_duplicates(),

        # --- LEARNING ---
        "learning":             all_pois[all_pois["amenity"].isin(["college", "school", "library", "kindergarten", "university", "training"])],

        # --- SUPPLIES ---
        "supplies":             all_pois[all_pois["shop"].isin(["department_store", "general", "mall", "supermarket", "convenience", "bakery", "butcher", "greengrocer", "books", "stationery", "clothes", "shoes", "appliance", "doityourself", "furniture", "electronics", "houseware"])],

        # --- EATING ---
        "eating":               all_pois[all_pois["amenity"].isin(["pub", "cafe", "restaurant", "fast_food", "food_court", "biergarten"])],

        # --- MOVING ---
        "moving":               all_pois[all_pois["public_transport"].isin(["platform", "station", "stop_position"])],

        # --- CULTURAL ACTIVITIES ---
        "cultural_activities":  pd.concat([
                                    all_pois[all_pois["amenity"].isin(["cinema", "community_centre", "theatre"])],
                                    all_pois[all_pois["tourism"].isin(["aquarium", "gallery", "museum", "zoo"])]
                                ]).drop_duplicates(),

        # --- PHYSICAL EXERCISE ---
        "physical_exercise":    all_pois[all_pois["leisure"].isin(["fitness_centre", "fitness_station", "sports_centre", "swimming_pool"])],

        # --- SERVICES ---
        "services":             all_pois[all_pois["amenity"].isin(["fire_station", "police", "post_office", "post_box", "townhall", "toilets"])],

        # --- HEALTHCARE ---
        "healthcare":           all_pois[all_pois["amenity"].isin(["clinic", "dentist", "doctors", "hospital", "pharmacy", "veterinary"])],

        # --- FINANCIAL ---
        "financial":            all_pois[all_pois["amenity"].isin(["atm", "bank", "payment_terminal", "payment_centre"])],
    }

    distance = args.distance   # max search distance (metres)
    #dist = 500        # threshold for counting a POI as "accessible"
    n["pois"] = 0

    frames = []
    if args.solo == None:
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
                num_pois=20,
            )
            nearest_pois[cat] = nearest_pois.sum(axis=1)
            nearest_pois = nearest_pois.iloc[:,-1:].truediv(20)
            #nearest_pois.columns = [cat]
    
            # Count nodes that have this category's nearest POI within threshold(deleted threshold, we ball)
            if cat == args.csvdebug: #(this is to insert zero rows, to examine feather output)
                nearest_pois[:] = 0
                n[cat] = nearest_pois[cat]
            else:
                n[cat] = nearest_pois[cat]
                n["pois"] += nearest_pois[cat]
            
            frames.append(nearest_pois)
    else:
        for cat, data in categories.items():
            if data.empty:
                continue
            if cat == args.solo:
                network.set_pois(
                    category=args.solo,
                    maxdist=distance,
                    maxitems=1000,
                    x_col=data.geometry.x,
                    y_col=data.geometry.y,
                )
        
                nearest_pois = network.nearest_pois(
                    distance=distance,
                    category=args.solo,
                    num_pois=20,
                )
                nearest_pois[args.solo] = nearest_pois.sum(axis=1)
                nearest_pois = nearest_pois.iloc[:,-1:].truediv(20)
                n[args.solo] = nearest_pois[args.solo]
                frames.append(nearest_pois)
    if not frames:
        raise RuntimeError("No POI categories had any data — feature CSV not written.")
    featurez = pd.concat(frames, axis=1, sort=False)
    featurez.index = featurez.index.map(featherIDtoOSMID)
    featurez.sort_index(inplace=True)
    featurez.index.name = None
    featurez.to_csv("./"+ args.output + "/" + args.title + "/featuresteis.csv", index=False)
    n["pois"] = n["pois"].truediv(len(frames))
    return n

# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Converts OSM BBOX or PLACES into FEATHER Compatible files"
    )
    
    
    parser.add_argument(
        "--title",
        type = str,
        required=True,
        help="Title for the project"
    )


    parser.add_argument(
        "--type",
        required=True,
        choices=["BBOX", "PLACE"],
        help="Conversion type"
    )

    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORD"),
        help="Bounding box coordinates"
    )

    parser.add_argument(
        "--place",
        type=str,
        help="Place name (only used if type=PLACE)"
    )
    
    parser.add_argument(
        "--solo",
        type=str,
        help="if you only want one tag cat, name it here(if none, all 10 categories will be saved to feature csv)"
    )
    parser.add_argument(
        "--distance",
        type=int,
        default=2000,
        help="the distance to look for out 20 pois per cat, this is alos used as vmax for the heatmap graph"
    )
    parser.add_argument(
        "--csvdebug",
        type=str,
        help="this takes a category name, and makes all rows of that zero(this is just to make spotting petterns in the feature csv easier, not for use with solo)"
    )
    
    parser.add_argument(
        "--output", 
        required=True,
        type=str,
        help="output direectory for the project folder"
        )
    

    args = parser.parse_args()

    if args.type == "BBOX" and not args.bbox:
        parser.error("--bbox is required when type=BBOX")

    if args.type == "PLACE" and not args.place:
        parser.error("--place is required when type=PLACE")

    Convert(args)
    

