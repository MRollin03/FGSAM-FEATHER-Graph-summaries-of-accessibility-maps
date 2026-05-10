import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox
import os


def Draw(G, nearest_pois, n, args):

    # attach geometries
    plot_gdf = gpd.GeoDataFrame(
        nearest_pois.copy(),
        geometry=n.geometry,
        crs=n.crs
    )

    fig, ax = ox.plot_graph(
        G,
        node_size=0,
        edge_color="#afdffe",
        edge_linewidth=0.6,
        bgcolor="#1a1a1a",
        show=False,
        close=False,
        figsize=(36, 34)
    )

    vmax = args.distance

    if args.solo is None:

        column = "all_pois"
        label = f"Average distance to any POIs ≤ {vmax} m"
        output_name = "all_pois.png"

    else:

        column = args.solo
        label = f"Average distance to {args.solo} ≤ {vmax} m"
        output_name = f"{args.solo}_pois.png"

    vmin = plot_gdf[column].min()

    plot_gdf.plot(
        ax=ax,
        column=column,
        cmap="plasma",
        markersize=3.5,
        alpha=0.8,
        legend=True,
        legend_kwds={
            "shrink": 0.5,
            "label": label,
            "orientation": "vertical"
        },
        vmin=vmin,
        vmax=vmax
    )

    out_path = os.path.join(
        args.output,
        args.title,
        output_name
    )

    plt.savefig(
        out_path,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close(fig)

    print(f"[info] Saved plot → {out_path}")