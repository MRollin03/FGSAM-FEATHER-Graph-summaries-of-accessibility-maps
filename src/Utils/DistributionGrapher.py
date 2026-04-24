import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from scipy.signal import savgol_filter
from scipy.interpolate import CubicSpline


CSV_FILE = "projects/Philadelphia/FeatherResult.csv"
OUTPUT = "./projects/Philadelphia/"
LABEL_COL = "Philadelphia"
ORDER=5
THETA_MAX=2.5
DISTANCE = 1500

#Helper functions
"""splits dataframe into two parts, devied by the median of the mean."""
def split_dataframe(dataframe):
    decider = np.median(dataframe.mean(axis=0))

    dataframe["is_high_median"] = dataframe.mean(axis=1) > decider #Add this temporary column
    #print(dataframe.mean(axis=1))
    #print(dataframe["is_high_median"])

    df_high = dataframe.loc[dataframe["is_high_median"] == True] #goes to higher if higher than median
    df_low  = dataframe.loc[dataframe["is_high_median"] == False] #same as above but for lower

    #Remove it again, dont know if this can be made better
    df_high = df_high.drop(columns=["is_high_median"], errors='ignore') 
    df_low = df_low.drop(columns=["is_high_median"], errors='ignore')

    return df_high, df_low

"""Returns the mean of df_high and df_low"""
def get_mean(df_high, df_low):
    return df_high.mean(axis=0), df_low.mean(axis=0) 

"""Returns the standard deviations of df_high and df_low"""
def get_std(df_high, df_low):
    return df_high.std(axis=0), df_low.std(axis=0)

"""Uniform plotting function, changes depending on if the graph is higher or the graph is lower"""
def High_low_plotter(order, mean, std, ax, theta, color): #isHigh,
    #NOTE: removed median, since very little variation, can be added again, if demmed necessary
    #if(isHigh):
    ax.plot(theta, mean, color=color, label=f"High order {order}")
    ax.fill_between(theta, mean - std, mean + std, color=color, alpha=0.4)
    """else:
        ax.plot(theta, mean, color=color, label=f"Low order {order}")
        ax.fill_between(theta, mean - std, mean + std, color=color, alpha=0.4)"""

    ax.set_xlim(0, THETA_MAX)
    ax.set_xlabel(r'Evaluation point: $\theta$')     
    ax.set_ylabel("CF Value")
    ax.set_ylim(-1.1,1.1) #adding a bit of padding

    print("plotting")
    return ax

features = ["outdoor_activities","learning","supplies","eating","moving","cultural_activities","physical_exercise","services","healthcare","financial","all_pois"]
color_arr = ["red", "blue", "green", "orange", "teal", "yellow", "grey", "brown", "purple", "pink", "black"]
levels = ["High", "Medium-High", "Medium", "Medium-low", "Low"]

#Drop imaginary columns

data = pd.read_csv(CSV_FILE)
data = data.drop(columns =['id'])

"""Drop imaginary columns, keeping only the "real" ones"""
imaginary = []
for col in data.columns:
    if "img" in col and col not in imaginary:
        imaginary.append(col)
data = data.drop(columns=imaginary)

def mean_for_single_feature_graph(feature):
    cool = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

    data_learning = pd.concat([data, cool], ignore_index=False, axis=1)

    dist5 = (DISTANCE / 5) #make the increments flex with distance
    incrementor = 0 

    df_list = []

    data_learning = data_learning.filter(like=feature)
    
    while incrementor < DISTANCE:
        incrementor += dist5
        #print(incrementor)

        tmp = data_learning[data_learning[feature] <= incrementor]
        tmp = tmp.sort_values(by=[feature])
        df_list.append(tmp)
    
        data_learning = data_learning[data_learning[feature] > incrementor]
        #print(f"data_learning:______  {data_learning}")


    #print(f"final: {df_list}")
    #print(len(df_list))
    _, axes = plt.subplots(5 ,1, figsize=(14, 5 * ORDER))
    count = 0
    for lst in df_list:
        #print(lst)
        
        lst = lst.drop(columns=[feature])
        part_mean = lst.mean(axis=1)

        theta = np.linspace(0, THETA_MAX, len(part_mean))
        std = lst.std(axis=1)

        axes[count].plot(theta, part_mean, color=color_arr[count], label=f"mean for {feature} ")
        axes[count].fill_between(theta, part_mean - std, part_mean + std, color=color_arr[count], alpha=0.4)
        axes[count].legend()

        axes[count].set_xlim(0, THETA_MAX)
        axes[count].set_xlabel(r'Evaluation point: $\theta$')     
        axes[count].set_ylabel("CF Value")
        axes[count].set_ylim(-1.1,1.1) 
        count +=1
    
    plt.tight_layout()
    plt.savefig(OUTPUT + f"{feature}meanwave")
        
for feature in features:
    mean_for_single_feature_graph(feature=feature)


def interpolate_dense(theta, y, factor=2):
    theta_dense = np.linspace(theta[0], theta[-1], len(theta) * factor)
    cs = CubicSpline(theta, y)
    return theta_dense, cs(theta_dense)

def Split_on_order(feature, eval_points=10):
    cool = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

    data_feature = data.filter(like=feature)

    _, axes = plt.subplots(ORDER, 1, figsize=(10, 5 * ORDER))
    for o in range(ORDER):
        start = int((o * eval_points))
        end = int(((o+1) *eval_points))

        data_subset = data_feature.iloc[:,start:end]
        data_subset = pd.concat([data_subset, cool.filter(like=feature)], ignore_index=False, axis=1)

        sorted_data = data_subset.sort_values(by=[feature])
        sorted_data = sorted_data.drop(columns=[feature])

        part_mean = sorted_data.mean(axis=1) #NOTE: was 1
        std = sorted_data.std(axis=1) #NOTE: was 1

        theta = np.linspace(0, THETA_MAX, len(part_mean))
        theta_smooth, re_smooth = interpolate_dense(theta, part_mean, factor=100)
        _, std_smooth = interpolate_dense(theta, std, factor=100)

        axes[o].plot(theta_smooth, re_smooth, color=color_arr[o])
        axes[o].fill_between(theta_smooth, re_smooth - std_smooth, re_smooth + std_smooth, color=color_arr[o], alpha=0.4)
        axes[o].set_xlim(0, THETA_MAX)
        axes[o].set_xlabel(r'Evaluation point: $\theta$')     
        axes[o].set_ylabel("CF Value")
        axes[o].set_ylim(-1.1,1.1) 
        axes[o].set_title(f"mean {feature} level {levels[o]} - {LABEL_COL}")
    
    
    plt.tight_layout()
    plt.savefig(OUTPUT + f"woop{feature}OverOrders")
"""
for feature in features:
    Split_on_order(feature) """

def percentage_split_graph():
    feat = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

    new_data = pd.concat([data, feat], ignore_index=False, axis=1)
    new_data['mean'] = new_data.mean(axis=1)
    sorted_data = new_data.sort_values('mean')

    long = sorted_data.shape[0]

    sorted_data = sorted_data.drop(columns=features)

    sorted_data = sorted_data.drop(columns=['mean'])

    df_bottom = sorted_data.head(int(long * 0.1))
    df_high = sorted_data.tail(int(long * 0.1))

    mean_high = df_high.mean(axis=1).values   
    mean_low  = df_bottom.mean(axis=1).values
    std_high  = df_high.std(axis=1).values
    std_low   = df_bottom.std(axis=1).values
                            
    theta = np.linspace(0, THETA_MAX, len(mean_high))
    
    theta_smooth, high_smooth = interpolate_dense(theta, mean_high, factor=100)
    _, low_smooth = interpolate_dense(theta, mean_low, factor=100)
    _, std_low_smooth = interpolate_dense(theta, std_low, factor=100)
    _, high_std_smooth = interpolate_dense(theta, std_high, factor=100)
    
    _, ax = plt.subplots(figsize=(18, 12))
            
    ax.plot(theta_smooth, high_smooth, color='blue', label='Top 10%')
    ax.fill_between(theta_smooth, high_smooth - high_std_smooth, high_smooth + high_std_smooth, color='blue', alpha=0.4)
    ax.set_xlim(0, THETA_MAX)
    ax.set_xlabel(r'Evaluation point: $\theta$')     
    ax.set_ylabel("CF Value")
    ax.set_ylim(-1.1,1.1) 
    ax.set_title(f"mean distribution for 10% highest and lowest - {LABEL_COL}")

    ax.plot(theta_smooth, low_smooth, color='red', label='Bottom 10%')
    ax.fill_between(theta_smooth, low_smooth - std_low_smooth, low_smooth + std_low_smooth, color='red', alpha=0.4)
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT + f"percentage")

percentage_split_graph()
