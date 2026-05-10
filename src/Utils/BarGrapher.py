#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 12:20:45 2026

@author: Teis
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# this is the bar grapher, the intent is to graph and quickly show a statistical display of the node distribution within a given accesiblilty csv.

CSV_FILE = "projects/.../featuresteis.csv"
OUTPUT = "./projects/.../"
LABEL_COL = "..."
DISTANCE = 2500  
data = pd.read_csv(CSV_FILE)
# We read the csv file here
# NOTE: this is not the post feather csv, but the pandana output.

# drop id col, it will not be needed.
data = data.drop(columns=['id'], errors='ignore') 

length = data.shape[0] ## get the length of our dataframe, we will need this for percentage calculations
feature_names = list(data.columns)
label_list = (" ", " ", " ", " ", " ") # for the graph labels
feature_dict = {
} # we will populate this dict with 5 percentage values for each feature
print("\n") 
print("length of dataframe:",  length)
print(feature_names)

## for loop on the feature names list, isolate the collum with said feature name.
## this loop sort the isolated column, and enter an inner loop, that chops the rows into 5 segments, and place them in our graph dictionary
for feature in feature_names:
    feature_df = data[feature]
    feature_df = feature_df.sort_values() 
    dist5 = (DISTANCE / 5) #make the increments flex with distance
    incrementor = 0 
    percentages = []
    totalp = 0 #check how much the tptal percentage adds to
    while incrementor < DISTANCE:
        incrementor += dist5
        if incrementor == DISTANCE:
            df1 = feature_df
            val = np.round((feature_df.shape[0]/length)*100,3)
        else:
            df1 = feature_df[feature_df <= incrementor]
            val = np.round((df1.shape[0]/length)*100,3)

        #print( incrementor , "m range percentage:", val)
        feature_df =  feature_df[feature_df > incrementor]
        percentages.append(val)
        totalp += val #due to the rounding this will not always be 100

    feature_dict[feature] = percentages
    print(feature,": adds to --> " ,totalp)
        

x = np.arange(len(label_list))  # the label locations
x = x*2
width = 1.25  # the width of the bars
multiplier = 0

fig, ax = plt.subplots(layout='constrained', figsize=(14,8))

for blabel, values in feature_dict.items():
    offset = (width * multiplier) *2
    rects = ax.bar(x + offset, values, width, label=blabel)
    ax.bar_label(rects, padding=3)
    multiplier += 5

# Add some text for labels, title and custom x-axis tick labels.
ax.set_ylabel('Percentage')
ax.set_title('Feature Distribution sorted for '+ LABEL_COL + ' by score and clustered by category')
ax.set_xticks((x + width)*11, label_list)
ax.set_xlabel('each category is sorted by order: High, Medium-High, Medium, Medium-Low, Low, each representing a 20% cutoff of score limit')
ax.legend(loc='upper left', ncols=6)
ax.set_ylim(0, 115)


fig.savefig(OUTPUT + LABEL_COL + "_Bar")