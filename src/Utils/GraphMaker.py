import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import networkx as nx
from scipy.interpolate import CubicSpline

# --- Load data ---
projectname = "Gilleleje"
df = pd.read_csv("projects/" + projectname + "/FeatherResult.csv")
features_meta = pd.read_csv("projects/" + projectname + "/featuresteis.csv")
feature_names = list(features_meta.columns)
n_features = len(feature_names)
feat0 = feature_names[0]

class Args:
    theta_max = 2.5
    order = 5

args = Args()

# Infer eval_points from actual CSV columns
base = f"{feature_names[0]}_real_0"
args.eval_points = len([c for c in df.columns
                        if c == base or c.startswith(base + ".")])
print(f"Inferred eval_points: {args.eval_points}")  # should be 25, 50, etc.

theta_pos = np.linspace(0.01, args.theta_max, args.eval_points)
theta_full = np.concatenate([-theta_pos[::-1], theta_pos])

def interpolate_dense(theta, y, factor=100):
    theta_dense = np.linspace(theta[0], theta[-1], len(theta) * factor)
    cs = CubicSpline(theta, y)
    return theta_dense, cs(theta_dense)

def get_cf_for_node(node_id, feature_idx, r):
    row = df[df["id"] == node_id].iloc[0]
    order_idx = r - 1
    feat = feature_names[feature_idx]

    base_real = f"{feat}_real_{order_idx}"
    base_img  = f"{feat}_img_{order_idx}"

    # Match base name + pandas duplicate suffixes (.1, .2, ...)
    real_cols = [c for c in df.columns 
                 if c == base_real or c.startswith(base_real + ".")]
    img_cols  = [c for c in df.columns 
                 if c == base_img  or c.startswith(base_img  + ".")]

    # Sort so .1, .2, ... are in theta order
    def sort_key(name, base):
        suffix = name[len(base):]
        return float(suffix[1:]) if suffix else 0.0

    real_cols = sorted(real_cols, key=lambda c: sort_key(c, base_real))
    img_cols  = sorted(img_cols,  key=lambda c: sort_key(c, base_img))

    print(f"r={r}, feat={feat}: found {len(real_cols)} real, {len(img_cols)} img cols")

    re_pos = row[real_cols].values.astype(float)
    im_pos = row[img_cols].values.astype(float)

    re_full = np.concatenate([ re_pos[::-1],  re_pos])
    im_full = np.concatenate([-im_pos[::-1],  im_pos])

    return re_full, im_full


# --- Find high/low degree nodes from the graph ---
"""
edges_df = pd.read_csv("projects/"+ projectname + "/FeatherEdges.csv")  # reads header automatically
print(edges_df.head())  # verify column names, e.g. 'u', 'v'

G = nx.from_pandas_edgelist(edges_df, source="u", target="v")

degrees = sorted(G.degree(), key=lambda x: x[1])
low_node_id  = degrees[0][0]
high_node_id = degrees[-1][0]

print(f"High degree node: {high_node_id} (degree {degrees[-1][1]})")
print(f"Low degree node:  {low_node_id}  (degree {degrees[0][1]})")
"""

# --- Find Highest and lowest sum scoring node ---
minid = features_meta.idxmin().values[0]
maxid = features_meta.idxmax().values[0]
minscore = features_meta.min()
maxscore = features_meta.max()

print("------------------")
print(f"Lowest score node: {minid} | Score:  {minscore}")

print(f"Highest score node: {maxid} | Score: {maxscore}")
print("------------------")

# --- Plot ---
colors = ["red", "blue", "green", "orange", "black"]
fig, axes = plt.subplots(2, 2, figsize=(10, 7))
fig.subplots_adjust(hspace=0.45, wspace=0.4)

node_ids = {
    "High score node": minid,
    "Low score node":  maxid,
}
feature_idx = 0  # log-degree or whichever feature to visualise

for row_idx, (node_label, node_id) in enumerate(node_ids.items()):
    for r in range(1, args.order + 1):
        re_full, im_full = get_cf_for_node(node_id, feature_idx, r)

        label = f"$r = {r}$"

        print(re_full)
        print("------")
        print(im_full)

        theta_smooth, re_smooth = interpolate_dense(theta_full, re_full)
        theta_smooth, im_smooth = interpolate_dense(theta_full, im_full)

        axes[row_idx, 0].plot(theta_smooth, re_smooth, color=colors[r-1], linewidth=1, label=label)
        axes[row_idx, 1].plot(theta_smooth, im_smooth, color=colors[r-1], linewidth=1, label=label)

    for col in range(2):
        ax = axes[row_idx, col]
        ax.set_title(node_label, fontsize=11)
        ax.set_xlim(-args.theta_max, args.theta_max)
        ax.set_ylim(-1.1, 1.1)
        ax.set_xlabel(r'Evaluation point $\theta$', fontsize=9)
        ax.axhline(0, color='black', linewidth=0.6)
        ax.axvline(0, color='black', linewidth=0.6)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))

    axes[row_idx, 0].set_ylabel(r'Re $\left(\mathrm{E}\left[e^{i\theta X}|G,u,r\right]\right)$', fontsize=9)
    axes[row_idx, 1].set_ylabel(r'Im $\left(\mathrm{E}\left[e^{i\theta X}|G,u,r\right]\right)$', fontsize=9)

handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=5,
           bbox_to_anchor=(0.5, 0.01), fontsize=9,
           frameon=True, edgecolor='black')

plt.savefig("characteristic_function.png", dpi=150, bbox_inches='tight')
plt.show()