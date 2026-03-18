#!/usr/bin/env python
# coding: utf-8

# In[1]:


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
else:
    n, e = ox.graph_to_gdfs(G)
    e = e.reset_index()

#places = ["silkeborg Municipality, Denmark",]


# These are tags with subtags or something don't know the terms
# Made this so we only have to get the features from the overpass API once!
tags = {
    "amenity": ["clinic", "pharmacy", "school"],
    "shop": ["supermarket", "convenience"]
}

all_pois = ox.features_from_bbox(bbox, tags=tags).to_crs(n.crs)
all_pois["geometry"] = all_pois.centroid
    
reducedpois = pd.DataFrame(all_pois, columns=["geometry","amenity", "education", "shop", "healthcare"])
reducedpois = reducedpois.droplevel("element")
reducedpois.to_csv("Features.csv")
        
reducededges = pd.DataFrame(e, columns=["u", "v"])
reducededges.to_csv("Edges.csv", index=False)

reducednode = pd.DataFrame(n, columns=["osmid"])
reducednode.to_csv("Node.csv", index=False)


featherIDtoOSMID = {}
counter = 0;
for index, row in reducededges.iterrows() :
    
    node1 = row['u']
    node2 = row['v']
    
    if not featherIDtoOSMID.__contains__(node1) : 
        featherIDtoOSMID.setdefault(node1, counter)
        counter += 1;
    
    if not featherIDtoOSMID.__contains__(node2) : 
        featherIDtoOSMID.setdefault(node2, counter)
        counter += 1;
        
    pass

convertedEdges = pd.DataFrame(columns = ['u', 'v']);

for index, row in reducededges.iterrows() :
    
    node1 = row['u']
    node2 = row['v']
    convertedEdges.loc[index] = [featherIDtoOSMID.get(node1), featherIDtoOSMID.get(node2)]
        
    pass

convertedPois = pd.DataFrame(columns=[ 'id', 'amenity', 'education', 'shop', 'healthcare'])
for index, row in reducedpois.iterrows():
    nearest_node = ox.nearest_nodes(G, row['geometry'].x, row['geometry'].y)

    nodeamenity   = 0 if type(row.get('amenity'))    is str else 0
    nodeeducation = 0 if type(row.get('education'))  is str else 0
    nodeshop      = 0 if type(row.get('shop'))       is str else 0
    nodehealthcare= 0 if type(row.get('healthcare')) is str else 0

    existing = convertedPois.loc[nearest_node] if nearest_node in convertedPois.index else [featherIDtoOSMID.get(nearest_node), 0, 0, 0, 0]
    convertedPois.loc[nearest_node] = [
        featherIDtoOSMID.get(nearest_node),
        max(existing[1], nodeamenity),
        max(existing[2], nodeeducation),
        max(existing[3], nodeshop),
        max(existing[4], nodehealthcare),
        ]
    
# Now fill in every node that had no nearby POI
for osmid, feather_id in featherIDtoOSMID.items():
    if osmid not in convertedPois.index:
        convertedPois.loc[osmid] = [feather_id, 0, 0, 0, 0]

convertedPois = convertedPois.sort_values('id')
convertedPois = convertedPois.drop("id", axis=1)

convertedPois.to_csv("2ConvertedFeatures.csv", index=False)
convertedEdges.to_csv("2ConvertedEdges.csv", index=False)

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
