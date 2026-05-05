#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import osmnx as ox
import os
import pandana as pdna
import pyproj

from shapely.ops import unary_union, transform
from shapely.geometry import box

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.timeout = 420

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
            G = ox.graph.graph_from_bbox(args.bbox, simplify=True, network_type="walk")

        elif args.type == "PLACE":
            G = ox.graph.graph_from_place(args.place, simplify=True, network_type="walk")

        elif args.type == "MULTI_PLACE":
            polygon = get_combined_polygon(args.places)
            G = ox.graph.graph_from_polygon(polygon, simplify=True, network_type="walk")

        ox.io.save_graphml(G, graphml_path)

    else:
        G = ox.io.load_graphml(graphml_path)

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
            "cinema", "community_centre", "theatre", "arts_centre", "events_venue", "exhibition_centre", "music_venue",
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

    if args.type == "BBOX":
        all_pois = ox.features_from_bbox(args.bbox, tags).to_crs(n.crs)

    elif args.type == "PLACE":
        all_pois = ox.features_from_place(args.place, tags).to_crs(n.crs)

    elif args.type == "MULTI_PLACE":
        polygon = get_combined_polygon(args.places)
        all_pois = ox.features_from_polygon(polygon, tags).to_crs(n.crs)

    all_pois["geometry"] = all_pois.centroid

    # -----------------------------------------------------------------------
    # ID Mapping
    # -----------------------------------------------------------------------

    featherIDtoOSMID = {osm_id: i for i, osm_id in enumerate(n.index)}

    edges_out = e[["u", "v"]].replace(featherIDtoOSMID)
    edges_out.to_csv(os.path.join(project_dir, "FeatherEdges.csv"), index=False)

    # -----------------------------------------------------------------------
    # FEATURES
    # -----------------------------------------------------------------------

    nearest_pois, featurez = ComputeFeatures(network, n, e, featherIDtoOSMID, all_pois, args)

    # -----------------------------------------------------------------------
    # HEATMAP
    # -----------------------------------------------------------------------

    fig, ax = ox.plot.plot_graph(
        G,
        node_size=0,
        edge_color="#afdffe",
        edge_linewidth=0.6,
        bgcolor="#1a1a1a",
        show=False,
        close=False,
        figsize=(36, 34)
    )

    if args.solo:
        column = args.solo
        label = f"Average distance to {args.solo} ≤ {args.distance} m"
        filename = f"{args.solo}_pois.png"
    else:
        column = "all_pois"
        label = f"Average distance to any POI ≤ {args.distance} m"
        filename = "all_pois.png"

    nearest_pois.plot(
        ax=ax,
        column=column,
        cmap="plasma",
        markersize=3.5,
        alpha=0.8,
        legend=True,
        legend_kwds={"shrink": 0.5, "label": label},
        vmin=nearest_pois[column].min(),
        vmax=2500
    )

    plt.savefig(os.path.join(project_dir, filename))
    plt.close()

    # -----------------------------------------------------------------------
    # GRAPH INFO
    # -----------------------------------------------------------------------

    info_path = os.path.join(project_dir, "graph_info.txt")

    num_nodes = len(n)
    num_edges = len(e)
    num_pois = len(all_pois)


    if args.type == "BBOX":
        west, south, east, north = args.bbox
        area_km2 = get_bbox_area_km2(west, south, east, north)
    else:
        area_km2 = all_pois.unary_union.convex_hull.area / 1_000_000

    node_density = num_nodes / area_km2 if area_km2 > 0 else 0
    poi_density = num_pois / area_km2 if area_km2 > 0 else 0

    if "all_pois" in nearest_pois.columns:
        best_idx = nearest_pois["all_pois"].idxmin()
        worst_idx = nearest_pois["all_pois"].idxmax()

        best_score = nearest_pois.loc[best_idx, "all_pois"]
        worst_score = nearest_pois.loc[worst_idx, "all_pois"]

        best_geom = nearest_pois.loc[best_idx].geometry
        worst_geom = nearest_pois.loc[worst_idx].geometry
    else:
        best_idx = worst_idx = None
    

    with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"Graph Information for {args.title}\n")
            f.write(f"===============================\n\n")
            f.write(f"Nodes: {num_nodes}\nEdges: {num_edges}\nPOIs: {num_pois}\n\n")
            f.write(f"Area (km^2): {area_km2:.3f}\n")
            f.write(f"Node density: {node_density:.3f}\n")
            f.write(f"POI density: {poi_density:.3f}\n")

            f.write("Best node (highest accessibility):\n")
            f.write(f"  OSM ID: {best_idx}\n")
            f.write(f"  Score: {best_score:.2f}\n")
            f.write(f"  Coordinates: ({best_geom.y:.6f}, {best_geom.x:.6f})\n\n")

            f.write("Worst node (lowest accessibility):\n")
            f.write(f"  OSM ID: {worst_idx}\n")
            f.write(f"  Score: {worst_score:.2f}\n")

    print(f"[info] Saved graph information → {info_path}")


# ---------------------------------------------------------------------------
# FEATURES
# ---------------------------------------------------------------------------

def ComputeFeatures(network, n, e, featherIDtoOSMID, all_pois, args):

    def filter_poi(df, col, values):
        if col in df.columns:
            return df[df[col].isin(values)]
        return pd.DataFrame(columns=df.columns)

    categories = {
        "outdoor_activities": pd.concat([
            filter_poi(all_pois, "leisure", ["park", "playground", "bathing_place", "garden", "pitch", "stadium", "swimming_area", "track"]),
            filter_poi(all_pois, "tourism", ["picnic_site"])
        ]).drop_duplicates(),

        "learning": filter_poi(all_pois, "amenity", ["college", "school", "library", "kindergarten", "university", "training"]),

        "supplies": filter_poi(all_pois, "shop", ["department_store", "general", "mall", "supermarket", "convenience", "bakery", "butcher", "greengrocer", "books", "stationery", "clothes", "shoes", "appliance", "doityourself", "furniture", "electronics", "houseware"]),

        "eating": filter_poi(all_pois, "amenity", ["pub", "cafe", "restaurant", "fast_food", "food_court", "biergarten"]),

        "moving": filter_poi(all_pois, "public_transport", ["platform", "station", "stop_position"]),

        "cultural_activities": pd.concat([
            filter_poi(all_pois, "amenity", ["cinema", "community_centre", "theatre"]),
            filter_poi(all_pois, "tourism", ["aquarium", "gallery", "museum", "zoo"])
        ]).drop_duplicates(),

        "physical_exercise": filter_poi(all_pois, "leisure", ["fitness_centre", "fitness_station", "sports_centre", "swimming_pool"]),

        "services": filter_poi(all_pois, "amenity", ["fire_station", "police", "post_office", "post_box", "townhall", "toilets"]),

        "healthcare": filter_poi(all_pois, "amenity", ["clinic", "dentist", "doctors", "hospital", "pharmacy", "veterinary"]),

        "financial": filter_poi(all_pois, "amenity", ["atm", "bank", "payment_terminal", "payment_centre"]),
    }

    n["all_pois"] = 0
    frames = []

    for cat, data in categories.items():
        if data.empty:
            continue

        network.set_pois(
            category=cat,
            maxdist=args.distance,
            maxitems=100,
            x_col=data.geometry.x,
            y_col=data.geometry.y,
        )

        nearest = network.nearest_pois(
            distance=args.distance,
            category=cat,
            num_pois=5
        )

        nearest[cat] = nearest.mean(axis=1)
        n[cat] = nearest[cat]
        n["all_pois"] += nearest[cat]

        frames.append(nearest[[cat]])

    if frames:
        n["all_pois"] /= len(frames)
        frames.append(n["all_pois"])

    featurez = pd.concat(frames, axis=1)
    featurez.index = featurez.index.map(featherIDtoOSMID)
    featurez.to_csv(os.path.join(args.output, args.title, "featureteis.csv"), index=False)

    return n, featurez

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--title", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--distance", type=int, default=2000)

    parser.add_argument("--type", required=True, choices=["BBOX", "PLACE", "MULTI_PLACE"])
    parser.add_argument("--bbox", nargs=4, type=float)
    parser.add_argument("--place")
    parser.add_argument("--places", nargs="+")
    parser.add_argument("--solo")

    args = parser.parse_args()

    if args.type == "BBOX" and not args.bbox:
        raise SystemExit("BBOX requires --bbox")

    if args.type == "PLACE" and not args.place:
        raise SystemExit("PLACE requires --place")

    if args.type == "MULTI_PLACE" and not args.places:
        raise SystemExit("MULTI_PLACE requires --places")

    Convert(args)