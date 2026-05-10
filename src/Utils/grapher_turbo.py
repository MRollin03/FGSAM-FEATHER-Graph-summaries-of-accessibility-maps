#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 12:20:45 2026

@author: Teis
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse

# this is my BALLER turbo grapher, the intent is to graph and quickly show a statistical display of the node distribution within a given accesiblilty csv.

CSV_FILE = "projects/bordeaux_20000_all/featuresteis.csv"
OUTPUT = "./projects/bordeaux_20000_all//"
LABEL_COL = "Bordeaux 1500m"
DISTANCE = 1500  #this is a surprize tool that will help us later. SHOULKD BE RENAMED TO SCORE_LIMIT
data = pd.read_csv(CSV_FILE)
## We read the csv file here, NOTE: this is not the post feather csv, but the pandana output.
### the initial version (this one) will only work with single feature .csv files. Later we will insert a function that allows multi col support.


    # drop id col, we will not need it.
    data = data.loc[:, ~data.columns.str.startswith('Unnamed')]
    data = data.drop(columns=['id'], errors='ignore')

    length = data.shape[0] ## get the length of our dataframe, we will need this for percentage calculations
    feature_names = list(data.columns)
    label_list = (" ", " ", " ", " ", " ") # for the graph labels, i dont want graph labels
    feature_dict = {
    } # we will populate this dict with 5 percentage values for each feature in a loop i haven't yet made
    print("\n") # give homie a lill space.
    print("length of dataframe:",  length)
    print(feature_names)
    ## after a quick check i can conclude that this does not count the header row :D

    ### okay this is the real sauce that be going down:

    ## the plan: we do a for loop on the feature names list, isolate the collum with said feature name.
    ## in this loop we then sort, the isolated colum, and enter a inner chop-shop loop.
    ## in this loop we use distance, to chop the rows into 5 segments, and place them in our graph dictionary( that i have not made yet)
    for feature in feature_names:
        jungle_is_massive = data[feature]#bring up the bass
        jungle_is_massive = jungle_is_massive.sort_values() #i tried to sort by, but as it's only one col it was stupid
        dist5 = (DISTANCE / 5) #make the increments flex with distance
        incrementor = 0 #you know who it is!
        funny = [] # it's ya boy, funny!
        totalp = 0 #this is just to check how much the tptal percentage adds to
        while incrementor < DISTANCE:
            incrementor += dist5
            if incrementor == DISTANCE:
                df1 = jungle_is_massive
                val = np.round((jungle_is_massive.shape[0]/length)*100,3)
            else:
                df1 = jungle_is_massive[jungle_is_massive <= incrementor]
                val = np.round((df1.shape[0]/length)*100,3)
            #print( incrementor , "m range percentage:", val)
            jungle_is_massive =  jungle_is_massive[jungle_is_massive > incrementor]
            funny.append(val)
            totalp += val #due to the rounding this will not always be 100
            ## now i need to populate feature dict with the 5 percentage values!
        # if feature in feature_dict:
        #     feature_dict[feature] = feature_dict[feature], val
        # else: 
        #     feature_dict[feature] = val
        
        #print(funny)
        feature_dict[feature] = funny
        print(feature,": adds to --> " ,totalp)
            
    # now i attempt a clumsy rewrite of the multi-nar example!

    x = np.arange(len(label_list))  # the label locations
    x = x*2
    width = 1.25  # the width of the bars
    multiplier = 0

    fig, ax = plt.subplots(layout='constrained', figsize=(14,8))

    for blabel, valuez in feature_dict.items():
        offset = (width * multiplier) *2
        rects = ax.bar(x + offset, valuez, width, label=blabel)
        ax.bar_label(rects, padding=3)
        multiplier += 5

# Add some text for labels, title and custom x-axis tick labels, etc.
ax.set_ylabel('Percentage')
ax.set_title('Feature Distribution sorted for '+ LABEL_COL + ' by score and clustered by category')
ax.set_xticks((x + width)*11, label_list)
ax.set_xlabel('each category is sorted by order: High, Medium-High, Medium, Medium-Low, Low, each representing a 20% cutoff of score limit')
ax.legend(loc='upper left', ncols=6)
ax.set_ylim(0, 115)


fig.savefig(OUTPUT + LABEL_COL + "_Bar")

# =============================================================================
# ## now we will use pandas "group by" to sort the values by distance, initially we will use 500m increments. as we expect max tistance to be 1500m or 2000m
# data = data.sort_values(by=["moving"])#just sort em???, i wanna
# df1 = data[data["moving"] <= 300] #this is gonna be ugly the first time around! will manually create each increment
# datanasty = data[data["moving"] > 300]
# ## divider for my sanity, first 300 done
# df2 = datanasty[(datanasty["moving"] <= 600)]
# datanasty = datanasty[datanasty["moving"] > 600]
# # 600m done
# df3 = datanasty[(datanasty["moving"] <= 900)]
# datanasty = datanasty[datanasty["moving"] > 900]
# #900m
# df4 = datanasty[(datanasty["moving"] <= 1200)]
# datanasty = datanasty[datanasty["moving"] > 1200]
# #1200m done, we just use datanasty for the remainder!
# 
# ## this is NASTY AF, pandana was not behaving when i wanted data in a range, so this is what we get :(
# ## once this works, we should up the resulution to 300m (or 200m)
# m_300 = np.round((df1.shape[0]/length)*100,3)
# m_600 = np.round((df2.shape[0]/length)*100,3)
# m_900 = np.round((df3.shape[0]/length)*100,3)
# m_1200 = np.round((df4.shape[0]/length)*100,3)
# m_1500 = np.round((datanasty.shape[0]/length)*100,3)
# ### looking at this garbage hurts my heart, so let's just quickly plot this in and go cry in a corner..
# 
# lables = ['<= 300m', '301-600m', '601-900m', '901-1200m', '1201-1500m']
# datarr = [m_300, m_600, m_900 , m_1200 , m_1500]
# plt.bar(lables, datarr)
# plt.title('Distribution of node distance to nearest moving poi')
# plt.xlabel('node groups')
# plt.ylabel('percentage')
# plt.show()
# ## this is the most basic bar graph for now, this will need to be beautified, but for now it is a proof of concept (keep telling yourself that)
# print(m_300)
# print(m_600)
# print(m_900)
# print(m_1200)
# print(m_1500) ## quick check if the percentage values are actually what they are supposed to be

# =============================================================================
# =============================================================================
# funnytoo = 1
# for feature in feature_names:
#     jungle_is_massive = data[feature]#bring up the bass
#     jungle_is_massive = jungle_is_massive.sort_values() #i tried to sort by, but as it's only one col it was stupid
#     print(feature, ": ")#print formatting
#     dist5 = (DISTANCE / 5) #make the increments flex with distance
#     incrementor = 0 #you know who it is!
#     funnythree = 0
#     while incrementor < DISTANCE:
#         funny = [] # it's ya boy, funny!
#         incrementor += dist5
#         df1 = jungle_is_massive[jungle_is_massive <= incrementor]
#         val = np.round((df1.shape[0]/length)*100,3)
#         #print( incrementor , "m range percentage:", val)
#         jungle_is_massive =  jungle_is_massive[jungle_is_massive > incrementor]
#         funny.append(val)
#         if funnytoo == 1:
#             feature_dict[label_list[funnythree]] = funny
#         else:
#             feature_dict[label_list[funnythree]].append(val) 
#         funnythree += 1
#        
#     funnytoo = 0
# print(feature_dict)
# =============================================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert OSM BBOX or PLACE into FEATHER-compatible files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    
    parser.add_argument(
        "--input",
        required=True,
        type=str,
        help="inputfolder where featureteis.csv is located",
    )
    
    parser.add_argument(    
        "--name",
        required=True,
        type=str,
        help="city name",
    )
    
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    plot(args)
else:
    plot(None)
    