import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import networkx as nx

# --- Load data ---
edges = pd.read_csv('input/edges/gradient_edges_21x21.csv', skiprows=[1])
features = pd.read_csv('output/outputtest.csv')  # do NOT skip row 1 — it's node 0

# --- Build graph ---
G = nx.Graph()
for _, row in edges.iterrows():
    G.add_edge(int(row['u']), int(row['v']))

# Grid layout (21 cols)
pos = {}
size = 21
for node in G.nodes():
    pos[node] = (node % size, -(node // size))

feat_indexed = features.set_index('id')

# --- Helper: magnitude for a node at (order, category) ---
def get_magnitude(node_id, cat, order, features_df):
    """Sum of |real| + |img| across all 25 eval points for given category/order."""
    real_cols = [c for c in features_df.columns if f'category{cat}_real_{order}' in c]
    img_cols  = [c for c in features_df.columns if f'category{cat}_img_{order}' in c]
    if node_id not in features_df.index:
        return 0.0
    row = features_df.loc[node_id]
    return float(row[real_cols].abs().sum() + row[img_cols].abs().sum())

# --- Plot settings ---
n_orders = 25  # FEATHER orders: 0–4
cat_labels = ['Category 1', 'Category 2', 'Category 3']
cat_cmaps  = ['Reds', 'Blues', 'Greens']

# --- Generate one figure per order ---
for order in range(n_orders):
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    fig.suptitle(f'FEATHER — Order {order}  (21×21 grid)', fontsize=15,
                 fontweight='bold', y=1.01)

    for col_idx, cat in enumerate([1, 2, 3]):
        ax = axes[col_idx]

        node_vals = {node: get_magnitude(node, cat, order, feat_indexed)
                     for node in G.nodes()}
        vals = np.array(list(node_vals.values()))
        norm = mcolors.Normalize(vmin=vals.min(), vmax=vals.max())
        cmap = plt.get_cmap(cat_cmaps[col_idx])

        node_colors = [cmap(norm(node_vals[n])) for n in G.nodes()]

        nx.draw(G, pos, ax=ax,
                with_labels=False,   # too many nodes for labels
                node_color=node_colors,
                node_size=60,        # small nodes for 441-node grid
                edge_color='#cccccc',
                width=0.5)

        ax.set_title(cat_labels[col_idx], fontsize=12)

        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        plt.colorbar(sm, ax=ax, fraction=0.04, pad=0.03)

    plt.tight_layout()
    plt.savefig(f'graph_order_{order}.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Saved graph_order_{order}.png")