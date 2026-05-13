import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CSV_FILE = "projects/.../FeatherResult.csv"
OUTPUT = "./projects/.../"
LABEL_COL = "..."
ORDER=5
# To Ordered graph
eval_points = 25 
dist = 20000 #this is for the plotting order graf, use the distance pandana was fed!
features = ["outdoor_activities","learning","supplies","eating","moving","cultural_activities","physical_exercise","services","healthcare","financial","all_pois"]
color_arr = ["red", "blue", "green", "orange", "teal", "yellow", "grey", "brown", "purple", "pink", "black"]
levels = ["High", "Medium-High", "Medium", "Medium-low", "Low"]

os.makedirs(OUTPUT, exist_ok=True)

data = pd.read_csv(CSV_FILE)
feat_csv = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

data = data.drop(columns =['id'])

"""Drop imaginary columns, keeping only the "real" ones"""
imaginary = []
for col in data.columns:
    if "real" in col and col not in imaginary:
        imaginary.append(col)
data = data.drop(columns=imaginary)

#Create wave diagram for a given feature
def Order_graph(feature):
    data_learning = pd.concat([data.reset_index(drop=True), feat_csv.reset_index(drop=True)],axis=1)
    tmp_lst = [] #make a list containing all "levels" of the order

    data_learning = data_learning.filter(like=feature)

    for o in range(ORDER):
        start = int((o * eval_points))
        end = int(((o+1) *eval_points))

        data_subset = data_learning.iloc[:,start:end]
        data_subset = pd.concat([data_subset, feat_csv.filter(like=feature)], ignore_index=False, axis=1)
        data_subset = data_subset.sort_values(by=[feature])
        data_subset.drop(columns=[feature])
        tmp_lst.append(data_subset)
    _, axes = plt.subplots(5 ,1, figsize=(10, 3 * ORDER))
    
    count = 0
    for df in tmp_lst:
        df = df.drop(columns=[feature])
        part_mean = df.mean(axis=1)

        theta = np.linspace(0, dist, len(part_mean))
        std = df.std(axis=1)
        axes[count].set_title(f"Mean distribution of {feature} - order {count+1} - {LABEL_COL}")
        axes[count].plot(theta, part_mean, color=color_arr[count], label=f"mean for {feature} evaluation points ")
        axes[count].fill_between(theta, part_mean - std, part_mean + std, color=color_arr[count], alpha=0.4)
        axes[count].legend()

        axes[count].set_xlabel(f"Distance: {dist}")     
        axes[count].set_ylabel("CF Value")
        axes[count].set_ylim(-1.1,1.1) 
        axes[count].set_xticklabels([])
        count +=1
    
    plt.tight_layout()
    plt.savefig(OUTPUT + f"{feature}_correct_meanwave_combined")

for feature in features:
    Order_graph(feature=feature)
