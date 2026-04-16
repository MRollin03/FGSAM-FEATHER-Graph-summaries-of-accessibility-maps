#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 12:20:45 2026

@author: Teis
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# this is my BALLER turbo grapher, the intent is to graph and quickly show a statistical display of the node distribution within a given accesiblilty csv.

CSV_FILE = "projects/bordeaux/featuresteis.csv"
OUTPUT = "./projects/bordeaux/"
LABEL_COL = "bordeaux"

data = pd.read_csv(CSV_FILE)
## We read the csv file here, NOTE: this is not the post feather csv, but the pandana putput.
### the initial version (this one) will only work with single feature .csv files. Later we will insert a function that allows multi col support.


# drop id col, we will not need it.
data = data.drop(columns=['id'], errors='ignore') #this does nothing :P

length = data.shape[0] ## get the length of our dataframe, we will need this for percentage calculations
print("\n") # give homie a lill space.
print("length of dataframe:",  length)
## after a quick check i can conclude that this does not count the header row :D

## now we will use pandas "group by" to sort the values by distance, initially we will use 500m increments. as we expect max tistance to be 1500m or 2000m
data = data.sort_values(by=["moving"])#just sort em???, i wanna
df1 = data[data["moving"] <= 300] #this is gonna be ugly the first time around! will manually create each increment
datanasty = data[data["moving"] > 300]
## divider for my sanity, first 300 done
df2 = datanasty[(datanasty["moving"] <= 600)]
datanasty = datanasty[datanasty["moving"] > 600]
# 600m done
df3 = datanasty[(datanasty["moving"] <= 900)]
datanasty = datanasty[datanasty["moving"] > 900]
#900m
df4 = datanasty[(datanasty["moving"] <= 1200)]
datanasty = datanasty[datanasty["moving"] > 1200]
#1200m done, we just use datanasty for the remainder!

## this is NASTY AF, pandana was not behaving when i wanted data in a range, so this is what we get :(
## once this works, we should up the resulution to 300m (or 200m)
m_300 = np.round((df1.shape[0]/length)*100,3)
m_600 = np.round((df2.shape[0]/length)*100,3)
m_900 = np.round((df3.shape[0]/length)*100,3)
m_1200 = np.round((df4.shape[0]/length)*100,3)
m_1500 = np.round((datanasty.shape[0]/length)*100,3)
### looking at this garbage hurts my heart, so let's just quickly plot this in and go cry in a corner..

lables = ['<= 300m', '301-600m', '601-900m', '901-1200m', '1201-1500m']
datarr = [m_300, m_600, m_900 , m_1200 , m_1500]
plt.bar(lables, datarr)
plt.title('Distribution of node distance to nearest moving poi')
plt.xlabel('node groups')
plt.ylabel('percentage')
plt.show()
## this is the most basic bar graph for now, this will need to be beautified, but for now it is a proof of concept (keep telling yourself that)
print(m_300)
print(m_600)
print(m_900)
print(m_1200)
print(m_1500) ## quick check if the percentage values are actually what they are supposed to be