import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import networkx as nx
from scipy.interpolate import CubicSpline
import argparse

# --- Argument Parser ---
parser = argparse.ArgumentParser(description="Plot Characteristic functions fra FEATHER noder")
parser.add_argument("--project", type=str, default="Copenhagen", help="Navn på projektet (mappe under projects/)")
parser.add_argument("--theta-max", type=float, default=2.5, help="Theta-max brugt i embedding")
parser.add_argument("--order", type=int, default=5, help="Order værdien for embeddings")
parser.add_argument("--interpolate", action="store_true", help="Brug CubicSpline til at udglatte kurverne")
args = parser.parse_args()

# --- Opsætning baseret på args ---
projectname = args.project
dointerpolation = args.interpolate

# --- Load data ---
df = pd.read_csv("projects/" + projectname + "/FeatherResult.csv")
features_meta = pd.read_csv("projects/" + projectname + "/featuresteis.csv")
feature_names = list(features_meta.columns)
n_features = len(feature_names)

os.makedirs("projects/" + projectname + "/characteristic_functions", exist_ok=True)

# Infer eval_points fra de faktiske CSV kolonner
# (Vi fjerner 'id' hvis den findes i listen for at finde den første rigtige feature)
check_feat = [f for f in feature_names if f != 'id'][0]
base = f"{check_feat}_real_0"
eval_points = len([c for c in df.columns if c == base or c.startswith(base + ".")])

print(f"Project: {projectname}")
print(f"Inferred eval_points: {eval_points}")

theta_pos = np.linspace(0.01, args.theta_max, eval_points)
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

    real_cols = sorted([c for c in df.columns if c == base_real or c.startswith(base_real + ".")], 
                       key=lambda x: float(x.split('.')[-1]) if '.' in x else 0)
    img_cols = sorted([c for c in df.columns if c == base_img or c.startswith(base_img + ".")], 
                      key=lambda x: float(x.split('.')[-1]) if '.' in x else 0)

    re_pos = row[real_cols].values.astype(float)
    im_pos = row[img_cols].values.astype(float)

    re_full = np.concatenate([ re_pos[::-1],  re_pos])
    im_full = np.concatenate([-im_pos[::-1],  im_pos])
    return re_full, im_full

# Find rækkerne med den laveste og højeste sum
row_sums = features_meta.select_dtypes(include=[np.number]).sum(axis=1)
min_idx = row_sums.idxmin()
max_idx = row_sums.idxmax()

# Hent de faktiske ID'er fra metadata (antager at der er en 'id' kolonne)
min_id = features_meta.loc[min_idx, 'id'] if 'id' in features_meta.columns else min_idx
max_id = features_meta.loc[max_idx, 'id'] if 'id' in features_meta.columns else max_idx

node_ids = {
    "High score node": max_id,
    "Low score node":  min_id,
}

# --- Plot alle features ---
for i, feat_name in enumerate(feature_names):
    if feat_name == "id": continue
    
    fig, axes = plt.subplots(len(node_ids), 2, figsize=(10, 7))
    fig.subplots_adjust(hspace=0.45, wspace=0.4)
    
    for row_idx, (node_label, n_id) in enumerate(node_ids.items()):
        for r in range(1, args.order + 1):
            re_full, im_full = get_cf_for_node(n_id, i, r)
            label = f"$r = {r}$"

            if dointerpolation:
                t_plot, re_plot = interpolate_dense(theta_full, re_full)
                _, im_plot = interpolate_dense(theta_full, im_full)
            else:
                t_plot, re_plot, im_plot = theta_full, re_full, im_full

            # Farve-logik
            if r == 1:
                color, lw, z = "red", 2, 5
            elif r == args.order:
                color, lw, z = "blue", 2, 4
            else:
                color, lw, z = "lightgrey", 1, 1

            axes[row_idx, 0].plot(t_plot, re_plot, color=color, linewidth=lw, label=label, zorder=z)
            axes[row_idx, 1].plot(t_plot, im_plot, color=color, linewidth=lw, label=label, zorder=z)

        # Formatering
        for col in range(2):
            ax = axes[row_idx, col]
            ax.set_title(f"{node_label} (ID: {int(n_id)})", fontsize=11)
            ax.set_xlim(-args.theta_max, args.theta_max)
            ax.set_ylim(-1.1, 1.1)
            ax.grid(True, alpha=0.3)
            ax.axhline(0, color='black', linewidth=0.6)
            ax.axvline(0, color='black', linewidth=0.6)

        axes[row_idx, 0].set_ylabel(r'Re $(\dots)$')
        axes[row_idx, 1].set_ylabel(r'Im $(\dots)$')

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    save_path = f"projects/{projectname}/characteristic_functions/feat_{feat_name}.png"
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close(fig)

print(f"Færdig! Billeder er gemt i projects/{projectname}/characteristic_functions/")
