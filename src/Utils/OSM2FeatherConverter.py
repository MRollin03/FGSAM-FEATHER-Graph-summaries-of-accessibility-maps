#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from types import SimpleNamespace
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import os
import pandana as pdna
import pyproj
import matplotlib

from shapely.ops import unary_union, transform
from shapely.geometry import box
from FEATHER.src import (
    main, 
    utils, 
    param_parser, 
    feather
)
import FeatherMapPlotter
import PandanaPlotter

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.timeout = 420
matplotlib.use('Agg')



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_combined_polygon(places):
    gdfs = [ox.geocode_to_gdf(p) for p in places]
    return unary_union([g.geometry.iloc[0] for g in gdfs])


def get_projected_area_km2(geom):
    project = pyproj.Transformer.from_crs(
        "EPSG:4326", "EPSG:32633", always_xy=True
    ).transform
    geom_projected = transform(project, geom)
    return geom_projected.area / 1_000_000


def get_bbox_area_km2(west, south, east, north):
    geom = box(west, south, east, north)
    return get_projected_area_km2(geom)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def Convert(args):

    project_dir  = os.path.join(args.output, args.title)
    os.makedirs(project_dir, exist_ok=True)

    graphml_path = os.path.join(project_dir, f"{args.title}.graphml")
    pandana_path = os.path.join(project_dir, f"{args.title}.h5")

    # -----------------------------------------------------------------------
    # GRAPH
    # -----------------------------------------------------------------------

    if not os.path.exists(graphml_path):

        if args.type == "BBOX":
            G = ox.graph_from_bbox(args.bbox, simplify=True, network_type="walk")
        elif args.type == "PLACE":
            G = ox.graph_from_place(args.place, simplify=True, network_type="walk")
        elif args.type == "MULTI_PLACE":
            polygon = get_combined_polygon(args.places)
            G = ox.graph_from_polygon(polygon, simplify=True, network_type="walk")

        ox.save_graphml(G, graphml_path)

    else:
        G = ox.load_graphml(graphml_path)

    G = ox.project_graph(G)
    n, e = ox.graph_to_gdfs(G)
    e = e.reset_index()

    # -----------------------------------------------------------------------
    # PANDANA
    # -----------------------------------------------------------------------

    if os.path.exists(pandana_path):
        network = pdna.Network.from_hdf5(pandana_path)
    else:
        network = pdna.Network(
            n.geometry.x, n.geometry.y,
            e["u"], e["v"],
            e[["length"]],
        )
        network.save_hdf5(pandana_path)

    # -----------------------------------------------------------------------
    # POIs
    # -----------------------------------------------------------------------

    tags = {
        "leisure": [
            "park", "playground", "bathing_place", "garden", "pitch",
            "stadium", "swimming_area", "track",
            "fitness_centre", "fitness_station", "sports_centre", "swimming_pool",
        ],
        "amenity": [
            "college", "school", "library", "kindergarten", "university", "training",
            "pub", "cafe", "restaurant", "fast_food", "food_court", "biergarten",
            "cinema", "community_centre", "theatre", "arts_centre", "events_venue",
            "exhibition_centre", "music_venue",
            "fire_station", "police", "post_office", "post_box", "townhall", "toilets",
            "clinic", "dentist", "doctors", "hospital", "pharmacy", "veterinary",
            "atm", "bank", "payment_terminal", "payment_centre",
        ],
        "shop": [
            "department_store", "general", "mall", "supermarket", "convenience",
            "bakery", "butcher", "greengrocer", "books", "stationery", "clothes",
            "shoes", "appliance", "doityourself", "furniture", "electronics", "houseware",
        ],
        "public_transport": ["platform", "station", "stop_position"],
        "tourism": ["aquarium", "gallery", "museum", "zoo", "picnic_site"],
    }

    if args.type == "BBOX":
        all_pois = ox.features_from_bbox(args.bbox, tags).to_crs(n.crs)
    elif args.type == "PLACE":
        all_pois = ox.features_from_place(args.place, tags).to_crs(n.crs)
    elif args.type == "MULTI_PLACE":
        polygon = get_combined_polygon(args.places)
        all_pois = ox.features_from_polygon(polygon, tags).to_crs(n.crs)

    all_pois["geometry"] = all_pois.centroid
    
    def filter_poi(df, col, values):
        if col in df.columns:
            return df[df[col].isin(values)]
        return pd.DataFrame(columns=df.columns)

    categories = {
            "outdoor_activities": pd.concat([
                filter_poi(all_pois, "leisure", ["park", "playground", "bathing_place",
                                                "garden", "pitch", "stadium",
                                                "swimming_area", "track"]),
                filter_poi(all_pois, "tourism", ["picnic_site"]),
            ]).drop_duplicates(),

            "learning": filter_poi(all_pois, "amenity", [
                "college", "school", "library", "kindergarten", "university", "training"
            ]),

            "supplies": filter_poi(all_pois, "shop", [
                "department_store", "general", "mall", "supermarket", "convenience",
                "bakery", "butcher", "greengrocer", "books", "stationery", "clothes",
                "shoes", "appliance", "doityourself", "furniture", "electronics", "houseware",
            ]),

            "eating": filter_poi(all_pois, "amenity", [
                "pub", "cafe", "restaurant", "fast_food", "food_court", "biergarten"
            ]),

            "moving": filter_poi(all_pois, "public_transport", [
                "platform", "station", "stop_position"
            ]),

            "cultural_activities": pd.concat([
                filter_poi(all_pois, "amenity", ["cinema", "community_centre", "theatre"]),
                filter_poi(all_pois, "tourism", ["aquarium", "gallery", "museum", "zoo"]),
            ]).drop_duplicates(),

            "physical_exercise": filter_poi(all_pois, "leisure", [
                "fitness_centre", "fitness_station", "sports_centre", "swimming_pool"
            ]),

            "services": filter_poi(all_pois, "amenity", [
                "fire_station", "police", "post_office", "post_box", "townhall", "toilets"
            ]),

            "healthcare": filter_poi(all_pois, "amenity", [
                "clinic", "dentist", "doctors", "hospital", "pharmacy", "veterinary"
            ]),

            "financial": filter_poi(all_pois, "amenity", [
                "atm", "bank", "payment_terminal", "payment_centre"
            ]),
        }

    # -----------------------------------------------------------------------
    # ID Mapping  (OSM ID -> integer 0..N-1)
    # -----------------------------------------------------------------------

    featherIDtoOSMID = {osm_id: i for i, osm_id in enumerate(n.index)}

    # Transform nodes
    nodes_out = n.copy()
    nodes_out.index = nodes_out.index.map(featherIDtoOSMID)
    nodes_out['x'] = nodes_out.geometry.x
    nodes_out['y'] = nodes_out.geometry.y

    # Transform and save edges
    edges_out = e[["u", "v"]].copy()
    edges_out["u"] = edges_out["u"].map(featherIDtoOSMID)
    edges_out["v"] = edges_out["v"].map(featherIDtoOSMID)
    edges_out["length"] = e["length"].round(3)
    edges_out.to_csv(os.path.join(project_dir, "FeatherEdges.csv"), index=False)

    # -----------------------------------------------------------------------
    # FEATURES
    # -----------------------------------------------------------------------
    
    if args.pandana > 0 :
        print("Pandana Feature Vectorization (SLOW!)")
        nearest_pois = PandanaSP(network, n, featherIDtoOSMID, categories, args )
        PandanaPlotter.Draw(G, nearest_pois, n, args)
    else :
        print("Binary Feature Vectorization")
        nearest_pois = MarkCategoryNodes(network, n, categories, featherIDtoOSMID, args)

    # -----------------------------------------------------------------------
    # GRAPH INFO FILE (Gathers infomation about graph)
    # -----------------------------------------------------------------------

    info_path = os.path.join(project_dir, "graph_info.txt")

    num_nodes = len(n)
    num_edges = len(e)
    num_pois  = len(all_pois)

    if args.type == "BBOX":
        west, south, east, north = args.bbox
        area_km2 = get_bbox_area_km2(west, south, east, north)
    else:
        area_km2 = all_pois.unary_union.convex_hull.area / 1_000_000

    node_density = num_nodes / area_km2 if area_km2 > 0 else 0
    poi_density  = num_pois  / area_km2 if area_km2 > 0 else 0

    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"Graph Information for {args.title}\n")
        f.write(f"===============================\n\n")
        f.write(f"Nodes: {num_nodes}\nEdges: {num_edges}\nPOIs: {num_pois}\n\n")
        f.write(f"Area (km^2): {area_km2:.3f}\n")
        f.write(f"Node density: {node_density:.3f}\n")
        f.write(f"POI density:  {poi_density:.3f}\n")

        if "all_pois" in nearest_pois.columns:
            # all_pois column is a count — higher = more categories present
            best_idx   = nearest_pois["all_pois"].idxmax()
            worst_idx  = nearest_pois["all_pois"].idxmin()
            best_score = nearest_pois.loc[best_idx,  "all_pois"]
            worst_score= nearest_pois.loc[worst_idx, "all_pois"]

            f.write("\nBest node (most categories covered):\n")
            f.write(f"  Feather ID: {best_idx}\n")
            f.write(f"  Score: {best_score}\n")
            f.write("\nWorst node (fewest categories covered):\n")
            f.write(f"  Feather ID: {worst_idx}\n")
            f.write(f"  Score: {worst_score}\n")

    print(f"[info] Saved graph information → {info_path}")
    
    # ----------------------------------------------------------------------
    # FEATHER embedding call
    # ----------------------------------------------------------------------
    
    featherargs = {
                  'title': args.title,
                  'BaseProjDir': args.output,
                  'graph_input' : args.output + '/'+ args.title + '/FeatherEdges.csv',
                  'feature_input': args.output + '/'+ args.title + '/Features.csv',
                  'output': args.output + '/'+ args.title +  '/FeatherResult.csv', 
                  'eval_points':args.eval_points,
                  'order': int(args.order),
                  'theta_max':args.theta_max,
                  'model_type': 'FEATHER',
                  }
    
    if not os.path.exists(args.output + '/'+ args.title + '/FeatherResult.csv'):
        main.main(SimpleNamespace(**featherargs))
    
    # ----------------------------------------------------------------------
    # PLOT  the Feather Results
    # ----------------------------------------------------------------------
    FeatherMapPlotter.Draw(SimpleNamespace(featherargs), G, featherIDtoOSMID)


# ---------------------------------------------------------------------------
# FEATURES — mark which nodes have a POI nearby per category
# ---------------------------------------------------------------------------

# No Shortpath calculations (aka "no pandana")
def MarkCategoryNodes(network, n, categories, featherIDtoOSMID, args):

    # Start with a zero DataFrame indexed by OSM node IDs
    n_features = pd.DataFrame(0, index=n.index, columns=list(categories.keys()))

    for cat, data in categories.items():
        if data.empty:
            print(f"[warn] No POIs found for category '{cat}' — column will be all 0.")
            continue

        # get_node_ids returns the nearest network node ID for each POI
        poi_node_ids = network.get_node_ids(
            data.geometry.x,
            data.geometry.y,
        )

        # Mark every node that is the nearest node to at least one POI
        valid_ids = poi_node_ids[poi_node_ids.isin(n_features.index)]
        n_features.loc[valid_ids, cat] = 1

    # Sum across categories (for nodes with multiple Amenities associated to it)
    n_features["all_pois"] = n_features[list(categories.keys())].sum(axis=1)

    # Remap OSM IDs to  Feather integer IDs before saving
    n_features.index = n_features.index.map(featherIDtoOSMID)
    n_features.index.name = "node_id"

    out_path = os.path.join(args.output, args.title, "Features.csv")
    n_features.to_csv(out_path)
    print(f"[info] Saved features → {out_path}")

    return n_features

def PandanaSP(network, n, featherIDtoOSMID, categories, args):
    
    n["all_pois"] = 0
    
    frames = []
    if args.solo == None:
        for cat, data in categories.items():
            if data.empty:
                continue
    
            network.set_pois(
                category=cat,
                maxdist=args.distance,
                maxitems=1000,
                x_col=data.geometry.x,
                y_col=data.geometry.y,
            )
    
            nearest_pois = network.nearest_pois(
                distance=args.distance,
                category=cat,
                num_pois=args.pandana,
            )
            nearest_pois[cat] = nearest_pois.sum(axis=1)
            nearest_pois = nearest_pois.iloc[:,-1:].truediv(args.pandana).round(3)
            
            n["all_pois"] += nearest_pois[cat]
            
            frames.append(nearest_pois)
    else:
        for cat, data in categories.items():
            if data.empty:
                continue
            if cat == args.solo:
                network.set_pois(
                    category=args.solo,
                    maxdist=args.distance,
                    maxitems=1000,
                    x_col=data.geometry.x,
                    y_col=data.geometry.y,
                )
        
                nearest_pois = network.nearest_pois(
                    distance=args.distance,
                    category=args.solo,
                    num_pois=args.pandana,
                )
                
                nearest_pois[args.solo] = nearest_pois.sum(axis=1)
                nearest_pois = nearest_pois.iloc[:,-1:].truediv(args.pandana)
                n[args.solo] = nearest_pois[args.solo]
                frames.append(nearest_pois)
    if not frames:
        raise RuntimeError("No POI categories had any data — feature CSV not written.")
    n["all_pois"] = n["all_pois"].truediv(len(frames))
    if args.solo == None:
        frames.append(n["all_pois"])    
    featurez = pd.concat(frames, axis=1, sort=False)
    featurez.index = featurez.index.map(featherIDtoOSMID)
    featurez.sort_index(inplace=True)
    featurez.index.name = None
    # EVIL code below, NOTE: this is meant to be used with a 10m distance in nearest_pois!
    # it should be noted that these fucked upo and evil functions replaces all instances of FALSE with the given value.
    #featurezz = featurez.where(featurez < 10,0) # all cells with no features within 10m are 10! so we replace em with zeroes
    #featurezz= featurez.where(featurez < 1,1) #replaces everything not below 1 with 1, now we have our evil and fucked up feature matrix
    #featurezz.to_csv("./"+ args.output + "/" + args.title + "/featuresEvil.csv", index=False)
    featurez.to_csv("./"+ args.output + "/" + args.title + "/Features.csv", index=False)

    return n

    

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    #- Conversion -#
    parser.add_argument("--title",    required=True)
    parser.add_argument("--output",   required=True)
    parser.add_argument("--distance", type=int, default=2000)
    parser.add_argument("--type",     required=True,
                        choices=["BBOX", "PLACE", "MULTI_PLACE"])
    parser.add_argument("--bbox",     nargs=4, type=float)
    parser.add_argument("--place")
    parser.add_argument("--places",   nargs="+")
    parser.add_argument("--solo")
    
    #- use pandana shortest path precalc - (SLOW!)
    parser.add_argument("--pandana", type=int, default=0)
    
    #- Feather Settings -#
    parser.add_argument("--eval-points", default=25)
    parser.add_argument("--order", default=5)
    parser.add_argument("--theta-max", default=2.5)

    args = parser.parse_args()

    if args.type == "BBOX"        and not args.bbox:   raise SystemExit("BBOX requires --bbox")
    if args.type == "PLACE"       and not args.place:  raise SystemExit("PLACE requires --place")
    if args.type == "MULTI_PLACE" and not args.places: raise SystemExit("MULTI_PLACE requires --places")

    Convert(args)