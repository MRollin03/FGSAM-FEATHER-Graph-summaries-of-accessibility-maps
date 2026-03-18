import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# ── Config — edit these ───────────────────────────────────────────────────────
CSV_FILE   = "../FEATHER/output/ourstuffresultthingy.csv"
METHOD     = "pca"       # "pca" or "tsne"
ID_COL     = "id"        # column with node IDs, or None
LABEL_COL  = None        # column to colour by, or None
OUTPUT     = None        # e.g. "plot.png" to save, or None to show inline
# ─────────────────────────────────────────────────────────────────────────────

# ── Load ──────────────────────────────────────────────────────────────────────
df = pd.read_csv(CSV_FILE)
print(f"Loaded {df.shape[0]} nodes × {df.shape[1]} columns")

meta_cols = [c for c in [ID_COL, LABEL_COL] if c and c in df.columns]
feature_cols = [c for c in df.columns if c not in meta_cols]
X = df[feature_cols].values.astype(float)
print(f"Feature matrix: {X.shape}")

# ── Reduce ────────────────────────────────────────────────────────────────────
if METHOD == "pca":
    reducer = PCA(n_components=2, random_state=42)
    coords  = reducer.fit_transform(X)
    var     = reducer.explained_variance_ratio_
    xlabel  = f"PC 1 ({var[0]*100:.1f}% var)"
    ylabel  = f"PC 2 ({var[1]*100:.1f}% var)"
    title   = "Node Embeddings — PCA"
else:
    perplexity = min(30, max(5, X.shape[0] // 3))
    reducer = TSNE(n_components=2, perplexity=perplexity,
                   random_state=42, init="pca", learning_rate="auto")
    coords  = reducer.fit_transform(X)
    xlabel, ylabel = "t-SNE 1", "t-SNE 2"
    title   = f"Node Embeddings — t-SNE (perplexity={perplexity})"

# ── Colour ────────────────────────────────────────────────────────────────────
if LABEL_COL and LABEL_COL in df.columns:
    labels        = df[LABEL_COL].values
    unique_labels = np.unique(labels)
    cmap          = plt.get_cmap("tab10", len(unique_labels))
    idx_map       = {l: i for i, l in enumerate(unique_labels)}
    colors        = [cmap(idx_map[l]) for l in labels]
    legend_handles = [
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor=cmap(i), markersize=8, label=str(l))
        for i, l in enumerate(unique_labels)
    ]
else:
    colors, legend_handles = coords[:, 0], None

node_ids = df[ID_COL].astype(str).values if ID_COL and ID_COL in df.columns \
           else [str(i) for i in range(len(coords))]

# ── Plot ──────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 7))

sc = ax.scatter(coords[:, 0], coords[:, 1],
                c=colors,
                cmap="viridis" if legend_handles is None else None,
                s=80, alpha=0.85, edgecolors="white", linewidths=0.5)

if len(node_ids) <= 40:
    for i, nid in enumerate(node_ids):
        ax.annotate(nid, (coords[i, 0], coords[i, 1]),
                    fontsize=7, xytext=(4, 4), textcoords="offset points", color="#444")

if legend_handles:
    ax.legend(handles=legend_handles, title=LABEL_COL,
              bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
else:
    fig.colorbar(sc, ax=ax, label=xlabel, shrink=0.7)

ax.set_xlabel(xlabel, fontsize=11)
ax.set_ylabel(ylabel, fontsize=11)
ax.set_title(title, fontsize=13, fontweight="normal", pad=12)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()

if OUTPUT:
    plt.savefig(OUTPUT, dpi=150, bbox_inches="tight")
    print(f"Saved → {OUTPUT}")
else:
    plt.show()