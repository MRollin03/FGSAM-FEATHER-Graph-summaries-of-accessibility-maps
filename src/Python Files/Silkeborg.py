#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import pandana as pdna
from pandana.loaders import osm
import numpy as np
import warnings
import matplotlib.pyplot as plt
from pathlib import Path
import geopandas as gpd
import osmnx as ox
import os
import timeit

ox.settings.use_cache = True
ox.settings.log_console = True

# In[2]:
#osmnx
filepath = "./data/silkbronx_network.graphml"
bbox = 9.48446, 56.15291, 9.62522, 56.20804
if(os.path.exists(filepath)):
    G = ox.io.load_graphml(filepath)
else:
    G = ox.graph.graph_from_bbox(bbox, simplify = True)  
    #G = ox.graph.graph_from_place("Silkeborg Municipality, Denmark")
    ox.io.save_graphml(G, filepath)

G = ox.project_graph(G)

#pandana
filepath_pan = "./data/silkbronx_features.h5"

if(os.path.exists(filepath_pan)):
    n, e = ox.graph_to_gdfs(G)
    e = e.reset_index()
    network = pdna.Network.from_hdf5(filepath_pan)
else:
    n, e = ox.graph_to_gdfs(G)
    e = e.reset_index()
    network = pdna.Network(n.geometry.x, n.geometry.y, e["u"], e["v"], e[["length"]])

    network.save_hdf5(filepath_pan)

#places = ["silkeborg Municipality, Denmark",]


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
    "pois_a": all_pois[all_pois["shop"].isin(["supermarket", "convenience"])],
    "pois_b": all_pois[all_pois["amenity"].isin(["clinic", "pharmacy"])],
    "pois_c": all_pois[all_pois["amenity"] == "school"],
    
    
    "pois_TURBO": all_pois # THIS MUST BE THE LAST ONE IN THE CATEGORY LIST!
}


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

# if its not the Teis mega special TURBO layer (Combined layer) just get the nearest node.
# else add the nearest node for each category to the combined if its in reach of the specifed value.
    if cat != "pois_TURBO":
        nearest = network.nearest_pois(distance=2000, category=cat, num_pois=1)
        n[cat] = (nearest <= 1000).sum(axis=1)
    else:
        turbo_sum = 0
        for sub_cat in ["pois_a", "pois_b", "pois_c"]:
            if sub_cat in categories:
                dist = network.nearest_pois(distance=2000, category=sub_cat, num_pois=1) # Number of nearst point for each category
                turbo_sum += (dist <= 1000).any(axis=1).astype(int) #add to the node value if its less than specified
        n["pois_TURBO"] = turbo_sum
        
dist = 1000


# In[3]:


fig, ax = ox.plot.plot_graph(
    G,
    node_size=0,
    edge_color="#afdffe",
    edge_linewidth=0.6,
    bgcolor="#1a1a1a",
    show=False,
    close=False,
    figsize=(16,14)
)

vmin = n["pois_a"].min()
vmax = n["pois_a"].max()

n.plot(
    ax=ax,
    column="pois_a",
    cmap="plasma",
    markersize=4,
    alpha=0.8,
    legend=True,
    legend_kwds={
        "shrink": 0.5,
        "label": f"Daily use accessibility ≤ {dist} m",
        "orientation": "vertical"
    },
    vmin=0,
    vmax=vmax
)

plt.show()

fig, ax = ox.plot.plot_graph(
    G,
    node_size=0,
    edge_color="#afdffe",
    edge_linewidth=0.6,
    bgcolor="#1a1a1a",
    show=False,
    close=False,
    figsize=(16,14)
)

vmin = n["pois_b"].min()
vmax = n["pois_b"].max()

n.plot(
    ax=ax,
    column="pois_b",
    cmap="plasma",
    markersize=4,
    alpha=0.8,
    legend=True,
    legend_kwds={
        "shrink": 0.5,
        "label": f"Healthcare accessiblilty ≤ {dist} m",
        "orientation": "vertical"
    },
    vmin=0,
    vmax=vmax
)

plt.show()

fig, ax = ox.plot.plot_graph(
    G,
    node_size=0,
    edge_color="#afdffe",
    edge_linewidth=0.6,
    bgcolor="#1a1a1a",
    show=False,
    close=False,
    figsize=(16,14)
)

vmin = n["pois_c"].min()
vmax = n["pois_c"].max()

n.plot(
    ax=ax,
    column="pois_c",
    cmap="plasma",
    markersize=4,
    alpha=0.8,
    legend=True,
    legend_kwds={
        "shrink": 0.5,
        "label": f"Education accesiblity ≤ {dist} m",
        "orientation": "vertical"
    },
    vmin=0,
    vmax=vmax
)

plt.show()
# this is an attempt to calculate accessibility on all available tags
fig, ax = ox.plot.plot_graph(
    G,
    node_size=0,
    edge_color="#afdffe",
    edge_linewidth=0.6,
    bgcolor="#1a1a1a",
    show=False,
    close=False,
    figsize=(16,14)
)

vmin = n["pois_TURBO"].min()
vmax = n["pois_TURBO"].max()

n.plot(
    ax=ax,
    column="pois_TURBO",
    cmap="plasma",
    markersize=4,
    alpha=0.8,
    legend=True,
    legend_kwds={
        "shrink": 0.5,
        "label": f"Mash up of all accesiblity ≤ {dist} m",
        "orientation": "vertical"
    },
    vmin=0,
    vmax=vmax
)

plt.show()

# In[4]:


#assemble the network fot the graph. Only look for nearest 1 poi (cred 2 jonas for the tech)
nearest_pois = network.nearest_pois(
    distance=2000,
    category="pois_a",
    num_pois=1,
)
n["pois"] = (nearest_pois <= dist).sum(axis=1)


nearest_pois = network.nearest_pois(
    distance=2000,
    category="pois_b",
    num_pois=1,
)
n["pois"] = n["pois"] + (nearest_pois <= dist).sum(axis=1)

nearest_pois = network.nearest_pois(
    distance=2000,
    category="pois_c",
    num_pois=1,
)
n["pois"] = n["pois"] + (nearest_pois <= dist).sum(axis=1)

# Now we plot the graph as usual. As we have 3 types, the graph max is 3. set it to 4 tho, because i felt like it.
fig, ax = ox.plot.plot_graph(
    G,
    node_size=0,
    edge_color="#afdffe",
    edge_linewidth=0.6,
    bgcolor="#1a1a1a",
    show=False,
    close=False,
    figsize=(16,14)
)

vmin = n["pois"].min()
vmax = n["pois"].max()

n.plot(
    ax=ax,
    column="pois",
    cmap="plasma",
    markersize=0.5,
    alpha=0.8,
    legend=True,
    legend_kwds={
        "shrink": 0.5,
        "label": f"Number of pois ≤ {dist} m",
        "orientation": "vertical"
    },
    vmin=0,
    vmax=4
)

plt.show()
