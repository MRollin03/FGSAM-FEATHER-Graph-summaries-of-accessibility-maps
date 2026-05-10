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
    # LOAD GRAPH
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

    print(f"Loading FEATHER features from: {args.output}")
    features = pd.read_csv(args.output, index_col=0)

    # -----------------------------------------------------------------------
    # PRE-COMPUTE ALL MAGNITUDES
    # -----------------------------------------------------------------------

    categories  = ['moving', "outdoor_activities", "learning","supplies", "eating", "cultural_activities","physical_exercise","financial", "healthcare", "services",'all_pois']
    orders      = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17.18,19,20] #Which orders you wish to be printed

    print("Pre-computing magnitudes (vectorised) ...")
    mag_cache = precompute_magnitudes(features, osm_node_ids, OSMID2Feather, categories, orders)
    print("Done.")

    # -----------------------------------------------------------------------
    # OUTPUT DIRECTORY
    # -----------------------------------------------------------------------

    out_dir = os.path.join(args.BaseProjDir, args.title, 'heatmaps')
    os.makedirs(out_dir, exist_ok=True)
        
    # -----------------------------------------------------------------------
    # GENERATE ONE FIGURE PER ORDER PER CATEGORY
    # -----------------------------------------------------------------------

    cmap = plt.get_cmap("plasma_r")

    for order in orders:
        for col_idx, cat in enumerate(categories):
            # Create figure for each category and real/img
            fig, ax = plt.subplots(figsize=(7, 5), facecolor='#111111')
            
            ax.set_facecolor('#111111')
            ax.set_aspect('equal')
            ax.axis('off')

            # HEader text for figure
            fig.suptitle(f'FEATHER Feature {cat} Magnitudes — Order {order}', 
                        fontsize=15, fontweight='bold', color='white', y=0.95)

            vals_array = mag_cache[(cat, order)]
            
            
            # Normalizing color values 
            vmin = np.percentile(vals_array, 5)
            vmax = np.percentile(vals_array, 97)
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

            # Road network
            ax.plot(flat_ex, flat_ey, color='#333333', linewidth=0.4, 
                    solid_capstyle='round', zorder=1)

            # Nodes
            ax.scatter(node_x, node_y, c=vals_array, cmap=cmap, norm=norm, 
                    s=0.5, linewidths=0, zorder=2, alpha=0.55)

            # Colorbar
            sm = cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = fig.colorbar(sm, ax=ax, fraction=0.035, pad=0.02)
            cbar.ax.yaxis.set_tick_params(color='white')
            plt.setp(cbar.ax.yaxis.get_ticklabels(), color='white')
            cbar.set_label('|real| + |imag| magnitude', color='white', fontsize=9)

            # Save 
            plt.tight_layout()
            
            cat_dir = os.path.join(out_dir, cat)
            os.makedirs(cat_dir, exist_ok=True) # Sikrer at mappen findes
            
            out_path = os.path.join(cat_dir, f'feather_order_{order}.png')
            plt.savefig(out_path, facecolor='#111111', bbox_inches='tight', dpi=600)
            plt.close(fig) 
            
            print(f"Saved: {out_path}")

    print(f"\nAll maps saved to: {out_dir}")
