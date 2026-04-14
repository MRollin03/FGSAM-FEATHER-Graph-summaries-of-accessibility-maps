import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re


# ── Config — edit these ───────────────────────────────────────────────────────
CSV_FILE   = "./FEATHER/output/København.csv"
OUTPUT     = "./images"        # e.g. "plot.png" to save, or None to show inline
LABEL_COL = "None"
SINGLE = -1
# ─────────────────────────────────────────────────────────────────────────────
# ─  Argument Parsing ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Makes pca Diagrams from Feather Output CSV's"
    )
    
    parser.add_argument(
        "--input",
        type = str,
        #required=True,
        help="input directory of feather csv"
    )

    parser.add_argument(
        "--title",
        type = str,
        #required=True,
        help="Title for the project"
    )
    
    parser.add_argument(
        "--output",
        type = str,
        #required=True,
        help="Output directory for the image"
    )

    parser.add_argument(
        "--eval-points",
        type = int,
        required=False,
        help="Number of evaluation points"
    )

    parser.add_argument(
        "--single",
        type = int,
        required=False,
        help="Making the graph for a single node, nodeid"
    )
    
args = parser.parse_args()

CSV_FILE = "Utils\projects\Aberdeen\FeatherResult.csv"
OUTPUT = "./projects/Aberdeen/"
LABEL_COL = "Aberdeen"

def clean_columns(dataframe):
    # drop id
    dataframe = dataframe.drop(columns=['id'], errors='ignore')
    # only match 'real' columns
    for col in dataframe.columns:
        if("real" not in col):
            dataframe = dataframe.drop(columns = [col], errors='ignore')
            continue
    return dataframe


# ── Load Feather CSV ─────────────────────────────────────────────────────────
df = pd.read_csv(CSV_FILE)

df_real = clean_columns(df)

print(df_real)

# avg and stds
feature_means = df_real.mean(axis=0)
feature_stds = df_real.std(axis=0)

print(feature_means)
print(feature_stds)

pls = np.arange(len(feature_means))

plt.figure(figsize=(10,8))
#plt.fill_between(eval_points, high, low, alpha=0.3)
plt.plot(pls, feature_means, label="eating", color="red")
plt.fill_between(pls, feature_means - feature_stds, feature_means + feature_stds, alpha=0.3, color="red")
plt.ylabel("Function Values")
plt.xlabel("Eval Points")
plt.ylim(-1,1)
plt.title(LABEL_COL)
plt.legend()
plt.show()






