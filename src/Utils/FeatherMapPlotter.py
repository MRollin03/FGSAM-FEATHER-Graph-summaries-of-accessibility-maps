#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
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


def build_feather_to_osm_mapping(feather_node_ids, osm_node_ids, featherIDtoOSMID):
    """
    Build feather_id -> osm_id mapping.

    Priority:
      1. Use featherIDtoOSMID dict if provided and non-empty.
      2. Fall back to positional alignment with a warning.
    """
    if featherIDtoOSMID:
        missing = [fid for fid in feather_node_ids if fid not in featherIDtoOSMID]
        if missing:
            print(f"WARNING: {len(missing)} FEATHER node(s) not in featherIDtoOSMID — will render as 0.")
        print(f"Using explicit featherIDtoOSMID mapping ({len(featherIDtoOSMID)} entries).")
        return featherIDtoOSMID

    # Positional fallback
    print("WARNING: No featherIDtoOSMID mapping provided — using positional alignment.")
    if len(feather_node_ids) != len(osm_node_ids):
        print(
            f"WARNING: FEATHER has {len(feather_node_ids)} nodes but OSM graph has "
            f"{len(osm_node_ids)} nodes. Only the first min(n) nodes will be matched."
        )
    n = min(len(feather_node_ids), len(osm_node_ids))
    return dict(zip(feather_node_ids[:n], osm_node_ids[:n]))


def precompute_magnitudes(features, osm_node_ids, osmid_to_feather, categories, orders):
    """
    Vectorised bulk computation of |real| + |imag| magnitudes.

    Returns
    -------
    mag_cache : dict  {(cat, order): np.ndarray shape (len(osm_node_ids),)}
        Values are aligned to osm_node_ids.
    """
    # Build the ordered list of feather IDs that correspond to osm_node_ids.
    # Missing mappings get None, which we resolve to NaN after reindex.
    feather_ids = [osmid_to_feather.get(osm_id) for osm_id in osm_node_ids]
    valid_mask  = np.array([fid is not None for fid in feather_ids])
    valid_fids  = [fid for fid in feather_ids if fid is not None]

    # Reindex the features DataFrame once so rows are in the same order as
    # osm_node_ids (unknown feather IDs become all-NaN rows).
    features_aligned = features.reindex(valid_fids)

    mag_cache = {}

    for cat in categories:
        for order in orders:
            # --- column selection (done once per (cat, order), not per node) ---
            real_cols = [c for c in features.columns if f'{cat}_real_{order}' in c]
            imag_cols = [c for c in features.columns if f'{cat}_img_{order}'  in c]

            if not real_cols and not imag_cols:
                # No matching columns → all zeros
                mag_cache[(cat, order)] = np.zeros(len(osm_node_ids), dtype=np.float32)
                continue

            # Bulk abs + sum across matching columns  (shape: n_valid_nodes,)
            real_sum = (features_aligned[real_cols].abs().sum(axis=1)
                        if real_cols else pd.Series(0.0, index=features_aligned.index))
            imag_sum = (features_aligned[imag_cols].abs().sum(axis=1)
                        if imag_cols else pd.Series(0.0, index=features_aligned.index))

            magnitude_valid = (real_sum + imag_sum).fillna(0.0).to_numpy(dtype=np.float32)

            # Scatter back into a full-length array (zeros for unmapped nodes)
            full = np.zeros(len(osm_node_ids), dtype=np.float32)
            full[valid_mask] = magnitude_valid
            mag_cache[(cat, order)] = full

    return mag_cache


# ---------------------------------------------------------------------------
# Main draw function
# ---------------------------------------------------------------------------

def Draw(G, OSMID2Feather):
    """
    Parameters
    ----------
    G              : networkx MultiDiGraph  (OSM road network)
    OSMID2Feather  : dict {osm_node_id: feather_node_id}
                     Pass an empty dict / None to fall back to positional alignment.
    """

    # -----------------------------------------------------------------------
    # PROJECT GRAPH + EXTRACT GEOMETRY
    # -----------------------------------------------------------------------

    nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)
    osm_node_ids = list(nodes_gdf.index)

    # Node positions (projected coordinates)
    node_x = nodes_gdf.geometry.x.to_numpy()
    node_y = nodes_gdf.geometry.y.to_numpy()

    # --- Vectorised edge geometry (avoids iterrows) ---
    # Each segment ends with a None sentinel so plt.plot draws separate lines.
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

    csv_path = os.path.join('projects', "Daegu, South Korea", 'FeatherResult.csv')
    print(f"Loading FEATHER features from: {csv_path}")
    features = pd.read_csv(csv_path, index_col=0)

    # -----------------------------------------------------------------------
    # BUILD OSMID → FEATHER MAPPING
    # -----------------------------------------------------------------------

    if not OSMID2Feather:
        # pair OSM nodes with feather nodes by position
        feather_ids = list(features.index)
        n = min(len(osm_node_ids), len(feather_ids))
        if len(osm_node_ids) != len(feather_ids):
            print(
                f"WARNING: OSM has {len(osm_node_ids)} nodes but FEATHER has "
                f"{len(feather_ids)} nodes. Matching first {n}."
            )
        OSMID2Feather = dict(zip(osm_node_ids[:n], feather_ids[:n]))

    # -----------------------------------------------------------------------
    # PRE-COMPUTE ALL MAGNITUDES (single bulk pass over the DataFrame)
    # -----------------------------------------------------------------------

    categories  = ['eating', 'all_pois']
    cat_labels  = ['Eating', 'All POIs']
    cat_cmaps   = ['plasma_r', 'Greens']
    orders      = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19]

    print("Pre-computing magnitudes (vectorised) ...")
    mag_cache = precompute_magnitudes(features, osm_node_ids, OSMID2Feather, categories, orders)
    print("Done.")

    # -----------------------------------------------------------------------
    # OUTPUT DIRECTORY
    # -----------------------------------------------------------------------

    out_dir = os.path.join("projects", "Daegu, South Korea", 'heatmaps')
    os.makedirs(out_dir, exist_ok=True)

    # -----------------------------------------------------------------------
    # GENERATE ONE FIGURE PER ORDER
    # -----------------------------------------------------------------------

    # Pre-fetch colormaps once (avoid repeated plt.get_cmap calls in the loop)
    cmaps = [plt.get_cmap(c) for c in cat_cmaps]

    for order in orders:
        fig, axes = plt.subplots(1, len(categories), figsize=(21, 8), facecolor='#111111')
        fig.suptitle(
            f'FEATHER Feature Magnitudes — Order {order}',
            fontsize=16, fontweight='bold', color='white', y=1.01
        )

        for col_idx, cat in enumerate(categories):
            ax   = axes[col_idx]
            cmap = cmaps[col_idx]

            ax.set_facecolor('#111111')
            ax.set_aspect('equal')
            ax.axis('off')

            vals_array = mag_cache[(cat, order)]
            vmin, vmax = vals_array.min(), vals_array.max()
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax if vmax > vmin else vmin + 1e-9)

            # Road network background
            ax.plot(flat_ex, flat_ey, color='#333333', linewidth=0.4,
                    solid_capstyle='round', zorder=1)

            # Scatter nodes coloured by magnitude
            ax.scatter(node_x, node_y, c=vals_array, cmap=cmap, norm=norm,
                       s=2, linewidths=0, zorder=2, alpha=0.7)

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
        plt.savefig(out_path, facecolor='#111111', bbox_inches='tight', dpi=300)
        print(f"Saved: {out_path}")
        plt.close(fig)

    print(f"\nAll {len(orders)} maps saved to: {out_dir}")


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

    # Load the graph (handles BBOX / PLACE / MULTI_PLACE + caching)
    G = load_graph(args)

    # No explicit ID mapping supplied → positional fallback inside Draw()
    Draw(G, OSMID2Feather={})