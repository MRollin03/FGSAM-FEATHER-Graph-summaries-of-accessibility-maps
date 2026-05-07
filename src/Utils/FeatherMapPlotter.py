#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import matplotlib
import osmnx as ox
import os

from shapely.ops import unary_union

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


def load_graph(args):
    """Load graph from GraphML file, or download and save it."""
    if args.graph and os.path.exists(args.graph):
        print(f"Loading graph from: {args.graph}")
        return ox.load_graphml(args.graph)

    print(f"Downloading OSM graph ({args.type}) ...")

    if args.type == "BBOX":
        if not args.bbox:
            raise ValueError("--bbox NORTH SOUTH EAST WEST is required for BBOX mode")
        G = ox.graph_from_bbox(args.bbox, simplify=True, network_type="walk")

    elif args.type == "PLACE":
        if not args.place:
            raise ValueError("--place is required for PLACE mode")
        G = ox.graph_from_place(args.place, simplify=True, network_type="walk")

    elif args.type == "MULTI_PLACE":
        if not args.places:
            raise ValueError("--places is required for MULTI_PLACE mode")
        polygon = get_combined_polygon(args.places)
        G = ox.graph_from_polygon(polygon, simplify=True, network_type="walk")

    if args.graph:
        os.makedirs(os.path.dirname(os.path.abspath(args.graph)), exist_ok=True)
        ox.save_graphml(G, args.graph)
        print(f"Graph saved to: {args.graph}")

    return G

import numpy as np

def precompute_magnitudes(features, osm_node_ids, osmid_to_feather, categories, orders):
    # Gets all of the id's from osm thats a part of the FeatherResult.csv
    feather_ids = [osmid_to_feather[osm_id] for osm_id in osm_node_ids]
    
    f_aligned = features.reindex(feather_ids)
    mag_cache = {}

    for cat in categories:
        for order in orders:
            # Seperate the columns by cat order and real/img
            r_cols = [c for c in f_aligned.columns if f'{cat}_real_{order}' in c]
            i_cols = [c for c in f_aligned.columns if f'{cat}_img_{order}' in c]

            #Calculate hte real and img sum of the evalpoints 
            r_sum = f_aligned[r_cols].abs().sum(axis=1).values if r_cols else 0
            i_sum = f_aligned[i_cols].abs().sum(axis=1).values if i_cols else 0
            
            #Sum the real and img values together for the combined magnitude
            mag_cache[(cat, order)] = (r_sum + i_sum)

    return mag_cache


# ---------------------------------------------------------------------------
# Main draw function
# ---------------------------------------------------------------------------

def Draw(args, G, OSMID2Feather):
    """
    Parameters
    G              : networkx MultiDiGraph  (OSM road network)
    OSMID2Feather  : dict, Dictionary with mapping of OSM to FeatherIDs
    """

    # -----------------------------------------------------------------------
    # PROJECT GRAPH
    # -----------------------------------------------------------------------

    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
    osm_node_ids = list(nodes_gdf.index)

    # Node positions (projected coordinates)
    node_x = nodes_gdf.geometry.x.to_numpy()
    node_y = nodes_gdf.geometry.y.to_numpy()

    # --- Vectorised edge geometry ---
    flat_ex, flat_ey = [], []
    for geom in edges_gdf.geometry:
        xs, ys = geom.xy
        flat_ex.extend(xs)
        flat_ex.append(None)
        flat_ey.extend(ys)
        flat_ey.append(None)

    print(f"Edges prepared: {len(edges_gdf)} segments.")

    # -----------------------------------------------------------------------
    # LOAD & INDEX FEATHER DATA
    # -----------------------------------------------------------------------

    csv_path = os.path.join(args.output, args.title, 'FeatherResult.csv')
    print(f"Loading FEATHER features from: {csv_path}")
    features = pd.read_csv(csv_path, index_col=0)

    # -----------------------------------------------------------------------
    # PRE-COMPUTE ALL MAGNITUDES
    # -----------------------------------------------------------------------

    categories  = ['moving', 'all_pois']
    cat_labels  = ['Moving', 'All POIs']
    cat_cmaps   = ['plasma_r','plasma_r']
    orders      = [0,1,2,3,4,5]

    print("Pre-computing magnitudes (vectorised) ...")
    mag_cache = precompute_magnitudes(features, osm_node_ids, OSMID2Feather, categories, orders)
    print("Done.")

    # -----------------------------------------------------------------------
    # OUTPUT DIRECTORY
    # -----------------------------------------------------------------------

    out_dir = os.path.join(args.output, args.title, 'heatmaps')
    os.makedirs(out_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # GENERATE ONE FIGURE PER ORDER
    # -----------------------------------------------------------------------

    # Get colormaps
    cmaps = [plt.get_cmap(c) for c in cat_cmaps]

    for order in orders:
        fig, axes = plt.subplots(1, len(categories), figsize=(14, 8), facecolor='#111111')
        fig.suptitle(
            f'FEATHER Feature Magnitudes — Order {order}',
            fontsize=15, fontweight='bold', color='white', y=1
        )

        for col_idx, cat in enumerate(categories):
            ax   = axes[col_idx]
            cmap = cmaps[col_idx]

            ax.set_facecolor('#111111')
            ax.set_aspect('equal')
            ax.axis('off')

            vals_array = mag_cache[(cat, order)]
            vmin, vmax = vals_array.min(), vals_array.max()
            print("vmin: " + str(vmin) + " vmax: "+ str(vmax))
            norm = mcolors.Normalize(vmin=vmin, vmax=math.floor(vmax))

            # Road network background
            ax.plot(flat_ex, flat_ey, color='#333333', linewidth=0.4,
                    solid_capstyle='round', zorder=1)

            # Scatter nodes coloured by magnitude
            ax.scatter(node_x, node_y, c=vals_array, cmap=cmap, norm=norm,
                       s=0.5, linewidths=0, zorder=2, alpha=0.55)

            ax.set_title(cat_labels[col_idx], fontsize=12, color='white', pad=6)

            # Colorbar
            sm = cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
            cbar.ax.yaxis.set_tick_params(color='white')
            plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')
            cbar.set_label('|real| + |imag| magnitude', color='white', fontsize=9)

        plt.tight_layout()
        out_path = os.path.join(out_dir, f'feather_order_{order}.png')
        plt.savefig(out_path, facecolor='#111111', bbox_inches='tight', dpi=600)
        print(f"Saved: {out_path}")
        plt.close(fig)

    print(f"\nAll maps saved to: {out_dir}")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Draw FEATHER feature magnitudes on an OSM road network."
    )
    parser.add_argument("--title",  required=True,
                        help="Project name — also resolves projects/<title>/FeatherResult.csv")
    parser.add_argument("--output", required=True,
                        help="Root output directory")
    parser.add_argument("--type",   required=True,
                        choices=["BBOX", "PLACE", "MULTI_PLACE"],
                        help="How to define the map area")
    parser.add_argument("--graph",  required=True,
                        help="Path to .graphml file. Loaded if it exists; downloaded + saved there if not.")

    parser.add_argument("--place",  default=None,
                        help="Place name for PLACE mode (e.g. 'Daegu, South Korea')")
    parser.add_argument("--places", nargs="+", default=None,
                        help="List of place names for MULTI_PLACE mode")
    parser.add_argument("--bbox",   nargs=4, type=float, default=None,
                        metavar=("NORTH", "SOUTH", "EAST", "WEST"),
                        help="Bounding box for BBOX mode")

    args = parser.parse_args()

    G = load_graph(args)
    Draw(G, OSMID2Feather={})