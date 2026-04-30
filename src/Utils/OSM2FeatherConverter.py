#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OSM → FEATHER feature converter
================================
Fetches a walkable street graph and points-of-interest from OpenStreetMap
for a given bounding box or place name, computes pandana-based accessibility
scores for up to 10 POI categories, writes a Feather-compatible feature CSV,
and saves a heatmap image.

ref: https://github.com/benedekrozemberczki/FEATHER

Usage examples
--------------
# By bounding box (west south east north):
python convert.py --title copenhagen --type BBOX \
    --bbox 12.52 55.66 12.62 55.69 \
    --output ./output --distance 1500

# By place name:
python convert.py --title aarhus --type PLACE \
    --place "Aarhus, Denmark" \
    --output ./output --distance 2000

# Single category only:
python convert.py --title aarhus --type PLACE \
    --place "Aarhus, Denmark" \
    --output ./output --solo healthcare

# Zero-out one category for debugging the feature CSV:
python convert.py --title aarhus --type PLACE \
    --place "Aarhus, Denmark" \
    --output ./output --csvdebug learning
"""

import argparse
import os

import matplotlib.pyplot as plt
import osmnx as ox
import pandana as pdna
import pandas as pd

from shapely.geometry import box
from shapely.ops import transform
import pyproj


ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.timeout = 600

# ---------------------------------------------------------------------------
# POI tag definitions
# ---------------------------------------------------------------------------

TAGS = {
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
    "public_transport": [
        "platform", "station", "stop_position",
    ],
    "tourism": [
        "aquarium", "gallery", "museum", "zoo",
        "picnic_site",
    ],
}

# ---------------------------------------------------------------------------
# Category definitions (used by ComputeFeatures)
# ---------------------------------------------------------------------------

def build_categories(all_pois):
    """Return a dict of category_name → filtered GeoDataFrame."""

    def fp(col, values):
        """Filter POIs by column membership; returns empty DF if col absent."""
        if col in all_pois.columns:
            return all_pois[all_pois[col].isin(values)]
        return pd.DataFrame(columns=all_pois.columns)

    return {
        "outdoor_activities": pd.concat([
            fp("leisure", ["park", "playground", "bathing_place", "garden",
                           "pitch", "stadium", "swimming_area", "track"]),
            fp("tourism", ["picnic_site"]),
        ]).drop_duplicates(),

        "learning": fp("amenity", [
            "college", "school", "library", "kindergarten", "university", "training",
        ]),

        "supplies": fp("shop", [
            "department_store", "general", "mall", "supermarket", "convenience",
            "bakery", "butcher", "greengrocer", "books", "stationery", "clothes",
            "shoes", "appliance", "doityourself", "furniture", "electronics", "houseware",
        ]),

        "eating": fp("amenity", [
            "pub", "cafe", "restaurant", "fast_food", "food_court", "biergarten",
        ]),

        "moving": fp("public_transport", [
            "platform", "station", "stop_position",
        ]),

        "cultural_activities": pd.concat([
            fp("amenity", ["cinema", "community_centre", "theatre"]),
            fp("tourism", ["aquarium", "gallery", "museum", "zoo"]),
        ]).drop_duplicates(),

        "physical_exercise": fp("leisure", [
            "fitness_centre", "fitness_station", "sports_centre", "swimming_pool",
        ]),

        "services": fp("amenity", [
            "fire_station", "police", "post_office", "post_box", "townhall", "toilets",
        ]),

        "healthcare": fp("amenity", [
            "clinic", "dentist", "doctors", "hospital", "pharmacy", "veterinary",
        ]),

        "financial": fp("amenity", [
            "atm", "bank", "payment_terminal", "payment_centre",
        ]),
    }


# ---------------------------------------------------------------------------
# Get area size
# ---------------------------------------------------------------------------

def get_bbox_area_km2(min_lon, min_lat, max_lon, max_lat):
    geom = box(min_lon, min_lat, max_lon, max_lat)

    wgs84 = pyproj.CRS("EPSG:4326")
    utm = pyproj.CRS("EPSG:32633")

    project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
    geom_projected = transform(project, geom)

    return geom_projected.area / 1_000_000
# ---------------------------------------------------------------------------
# ID mapping
# ---------------------------------------------------------------------------

def build_id_map(n):
    """
    Map OSM node IDs (n.index) to sequential integer IDs starting at 0.

    Returns
    -------
    dict  {osm_id: feather_int_id}
    """
    return {osm_id: i for i, osm_id in enumerate(n.index)}


# ---------------------------------------------------------------------------
# Edge conversion
# ---------------------------------------------------------------------------

def osm_edges_to_feather(edges, id_map, output_path):
    """
    Replace OSM node IDs in the edge list with sequential Feather IDs
    and write the result to *output_path*.

    Parameters
    ----------
    edges       : pd.DataFrame  — must contain columns 'u' and 'v'
    id_map      : dict          — {osm_id: feather_int_id}
    output_path : str           — destination CSV path
    """
    if not id_map:
        raise ValueError("id_map is empty — no nodes found in graph.")
    if edges.empty:
        raise ValueError("Edge list is empty.")

    converted = edges[["u", "v"]].replace(id_map)
    converted.to_csv(output_path, index=False)
    print(f"[edges] Wrote {len(converted)} edges → {output_path}")


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

def compute_features(network, n, id_map, all_pois, distance, solo, csvdebug, out_csv):
    categories = build_categories(all_pois)
    n["pois"] = 0
    frames = []

    if solo:
        # --- single-category fast path -----------------------------------
        cat_data = categories.get(solo)
        if cat_data is None or cat_data.empty:
            raise RuntimeError(f"No POI data found for solo category {solo!r}.")
        
        network.set_pois(
            category=solo,
            maxdist=distance,
            maxitems=1000,
            x_col=data.geometry.x,
            y_col=data.geometry.y,
        )
        nearest = network.nearest_pois(distance=distance, category=solo, num_pois=20)
        
        # Beregn gennemsnit
        nearest[solo] = nearest.sum(axis=1).truediv(20).round(3)
        
        # NYT: Nulstil noder der er POIs i denne kategori
        poi_node_ids = network.get_node_ids(data.geometry.x, data.geometry.y)
        nearest.loc[poi_node_ids, solo] = 0

        if cat == csvdebug:
            nearest[cat] = 0
        
        n[cat] = nearest[cat]
        n["pois"] += nearest[cat]
        frames.append(nearest[[cat]])
    else:
        # --- all-categories path -----------------------------------------
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
            nearest = network.nearest_pois(distance=distance, category=cat, num_pois=20)
            
            # Beregn gennemsnit
            nearest[cat] = nearest.sum(axis=1).truediv(20).round(3)
            
            # NYT: Nulstil noder der er POIs i denne kategori
            poi_node_ids = network.get_node_ids(data.geometry.x, data.geometry.y)
            nearest.loc[poi_node_ids, cat] = 0

            if cat == csvdebug:
                nearest[cat] = 0
            
            n[cat] = nearest[cat]
            n["pois"] += nearest[cat]
            frames.append(nearest[[cat]])

    # ... resten af din eksisterende logik (concat, map id_map, save csv) ...
    featurez = pd.concat(frames, axis=1, sort=False)
    featurez.index = featurez.index.map(id_map)
    featurez.to_csv(out_csv, index=False)

    lowestAndHighest(featurez, id_map)
    
    if not solo:
        n["pois"] = n["pois"].truediv(len(frames))
    return n



# ---------------------------------------------------------------------------
# Heatmap plotting
# ---------------------------------------------------------------------------

def save_heatmap(G, n, column, vmax, label, out_path):
    """
    Overlay a scatter heatmap of *column* values on the street graph and
    save the figure to *out_path*.
    """
    fig, ax = ox.plot.plot_graph(
        G,
        node_size=0,
        edge_color="#afdffe",
        edge_linewidth=0.6,
        bgcolor="#1a1a1a",
        show=False,
        close=False,
        figsize=(36, 34),
    )
    vmin = n[column].min()
    n.plot(
        ax=ax,
        column=column,
        cmap="plasma",
        markersize=3.5,
        alpha=0.8,
        legend=True,
        legend_kwds={
            "shrink": 0.5,
            "label": label,
            "orientation": "vertical",
        },
        vmin=vmin,
        vmax=vmax,
    )
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot] Saved heatmap → {out_path}")


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def convert(args):
    """
    Full pipeline:
      1. Load or download OSM graph (.graphml cache)
      2. Load or build pandana network (.h5 cache)
      3. Fetch POIs from Overpass
      4. Build OSM→Feather ID mapping
      5. Write FeatherEdges.csv
      6. Compute per-category accessibility features
      7. Write feature CSV
      8. Save heatmap PNG
    """
    if args.title is None:
        raise ValueError("--title is required.")

    project_dir = os.path.join(args.output, args.title)
    os.makedirs(project_dir, exist_ok=True)

    graphml_path = os.path.join(project_dir, f"{args.title}.graphml")
    pandana_path = os.path.join(project_dir, f"{args.title}.h5")
    edges_csv    = os.path.join(project_dir, "FeatherEdges.csv")
    features_csv = os.path.join(project_dir, "featuresteis.csv")

    # ------------------------------------------------------------------
    # 1. Graph
    # ------------------------------------------------------------------
    if not os.path.exists(graphml_path):
        print("[graph] Downloading OSM graph …")
        if args.type == "BBOX":
            G = ox.graph.graph_from_bbox(args.bbox, simplify=True, network_type="walk")
        else:
            G = ox.graph.graph_from_place(args.place, simplify=True, network_type="walk")
        ox.io.save_graphml(G, graphml_path)
        print(f"[graph] Saved → {graphml_path}")
    else:
        print(f"[graph] Loading cached graph from {graphml_path}")
        G = ox.io.load_graphml(graphml_path)

    G = ox.project_graph(G)
    n, e = ox.graph_to_gdfs(G)
    e = e.reset_index()

    # ------------------------------------------------------------------
    # 2. Pandana network
    # ------------------------------------------------------------------
    if os.path.exists(pandana_path):
        print(f"[pandana] Loading cached network from {pandana_path}")
        network = pdna.Network.from_hdf5(pandana_path)
    else:
        print("[pandana] Building network …")
        network = pdna.Network(
            n.geometry.x, n.geometry.y,
            e["u"], e["v"],
            e[["length"]],
        )
        network.save_hdf5(pandana_path)
        print(f"[pandana] Saved → {pandana_path}")

    # ------------------------------------------------------------------
    # 3. POIs
    # ------------------------------------------------------------------
    print("[pois] Fetching POIs from Overpass …")
    if args.type == "BBOX":
        all_pois = ox.features_from_bbox(args.bbox, TAGS).to_crs(n.crs)
    else:
        all_pois = ox.features_from_place(args.place, TAGS).to_crs(n.crs)
    all_pois["geometry"] = all_pois.centroid
    print(f"[pois] {len(all_pois)} POIs fetched.")

    info_path = os.path.join(project_dir, "graph_info.txt")

    num_nodes = len(n)
    num_pois = len(all_pois)

    if args.type == "BBOX":
        west, south, east, north = args.bbox
        area_km2 = get_bbox_area_km2(west, south, east, north)
    else:
        area_km2 = all_pois.unary_union.convex_hull.area / 1_000_000

    node_density = num_nodes / area_km2 if area_km2 > 0 else 0
    poi_density = num_pois / area_km2 if area_km2 > 0 else 0

    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"Graph Information for {args.title}\n")
        f.write(f"===============================\n")
        f.write(f"Number of nodes: {num_nodes}\n")
        f.write(f"Number of POIs: {num_pois}\n")
        f.write(f"Area (km^2): {area_km2:.3f}\n")
        f.write(f"Node density (nodes/km^2): {node_density:.3f}\n")
        f.write(f"POI density (POIs/km^2): {poi_density:.3f}\n")

    print(f"[info] Saved graph information → {info_path}")
    # ------------------------------------------------------------------
    # 4. ID mapping
    # ------------------------------------------------------------------
    id_map = build_id_map(n)

    # ------------------------------------------------------------------
    # 5. Edge CSV
    # ------------------------------------------------------------------
    reduced_edges = pd.DataFrame(e, columns=["u", "v"])
    osm_edges_to_feather(reduced_edges, id_map, edges_csv)

    # ------------------------------------------------------------------
    # 6 & 7. Features
    # ------------------------------------------------------------------
    n = compute_features(
        network=network,
        n=n,
        id_map=id_map,
        all_pois=all_pois,
        distance=args.distance,
        solo=args.solo,
        csvdebug=args.csvdebug,
        out_csv=features_csv,
    )
    # ------------------------------------------------------------------
    # 8. Graph information files
    # ------------------------------------------------------------------
    info_path = os.path.join(project_dir, "graph_info.txt")

    num_nodes = len(n)
    num_pois = len(all_pois)

    if args.type == "BBOX":
        west, south, east, north = args.bbox
        area_km2 = get_bbox_area_km2(west, south, east, north)
    else:
        area_km2 = all_pois.unary_union.convex_hull.area / 1_000_000

    node_density = num_nodes / area_km2 if area_km2 > 0 else 0
    poi_density = num_pois / area_km2 if area_km2 > 0 else 0

    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"Graph Information for {args.title}\n")
        f.write(f"===============================\n")
        f.write(f"Number of nodes: {num_nodes}\n")
        f.write(f"Number of POIs: {num_pois}\n")
        f.write(f"Area (km^2): {area_km2:.3f}\n")
        f.write(f"Node density (nodes/km^2): {node_density:.3f}\n")
        f.write(f"POI density (POIs/km^2): {poi_density:.3f}\n")

    print(f"[info] Saved graph information → {info_path}")
    # ------------------------------------------------------------------
    # 9. Heatmap
    # ------------------------------------------------------------------
    if args.solo:
        column   = args.solo
        img_path = os.path.join(project_dir, f"{args.solo}_pois.png")
        label    = f"Average distance to {args.solo} ≤ {args.distance} m"
    else:
        column   = "pois"
        img_path = os.path.join(project_dir, "all_pois.png")
        label    = f"Average distance to any POI ≤ {args.distance} m"

    save_heatmap(G, n, column=column, vmax=args.distance, label=label, out_path=img_path)

    print("[done] All outputs written to:", project_dir)

def lowestAndHighest(featurez, id_map):
    
    reverse_map = {v: k for k, v in id_map.items()}

    # Beregn summen af distancer for hver node
    row_sums = featurez.sum(axis=1)

    min_id = row_sums.idxmin()
    max_id = row_sums.idxmax()

    min_score = row_sums.min()
    max_score = row_sums.max()

    print("--- Tilgængeligheds-ekstremer ---")
    # Laveste score = Kortest gennemsnitsafstand (Bedst tilgængelighed)
    print(f"Bedst (lavest dist): ID: {min_id} | osmID: {reverse_map.get(min_id, 'N/A')} | Score: {min_score:.2f}")
    
    # Højeste score = Længst gennemsnitsafstand (Dårligst tilgængelighed)
    print(f"Værst (højest dist): ID: {max_id} | osmID: {reverse_map.get(max_id, 'N/A')} | Score: {max_score:.2f}")
    print("--------------------------------")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert OSM BBOX or PLACE into FEATHER-compatible files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--title",
        type=str,
        required=True,
        help="Project name — used for the output sub-directory and file names.",
    )
    parser.add_argument(
        "--type",
        required=True,
        choices=["BBOX", "PLACE"],
        help="Whether to query by bounding box or place name.",
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
        help="Bounding box coordinates (required when --type BBOX).",
    )
    parser.add_argument(
        "--place",
        type=str,
        help="Place name passed to Nominatim (required when --type PLACE).",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=str,
        help="Root output directory; project files go into <output>/<title>/.",
    )
    parser.add_argument(
        "--distance",
        type=int,
        default=2000,
        help=(
            "Maximum walking distance (metres) when searching for POIs. "
            "Also used as the colour-scale upper bound on the heatmap. "
            "Default: 2000."
        ),
    )
    parser.add_argument(
        "--solo",
        type=str,
        default=None,
        help=(
            "Process only this one category "
            "(outdoor_activities | learning | supplies | eating | moving | "
            "cultural_activities | physical_exercise | services | healthcare | financial). "
            "If omitted all 10 categories are processed."
        ),
    )
    parser.add_argument(
        "--csvdebug",
        type=str,
        default=None,
        help=(
            "Zero out all rows of this category in the feature CSV "
            "(makes patterns in other columns easier to spot). "
            "Incompatible with --solo."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.type == "BBOX" and not args.bbox:
        raise SystemExit("Error: --bbox is required when --type BBOX.")
    if args.type == "PLACE" and not args.place:
        raise SystemExit("Error: --place is required when --type PLACE.")
    if args.solo and args.csvdebug:
        raise SystemExit("Error: --solo and --csvdebug cannot be used together.")

    convert(args)