import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline


CSV_FILE = "projects/Daegu/FeatherResult.csv"
OUTPUT = "./projects/Daegu/"
LABEL_COL = "Daegu"
ORDER=5
THETA_MAX=2.5
DISTANCE = 2000

features = ["outdoor_activities","learning","supplies","eating","moving","cultural_activities","physical_exercise","services","healthcare","financial","all_pois"]
color_arr = ["red", "blue", "green", "orange", "teal", "yellow", "grey", "brown", "purple", "pink", "black"]
levels = ["High", "Medium-High", "Medium", "Medium-low", "Low"]

data = pd.read_csv(CSV_FILE)
feat_csv = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

data = data.drop(columns =['id'])

"""Drop imaginary columns, keeping only the "real" ones"""
imaginary = []
for col in data.columns:
    if "img" in col and col not in imaginary:
        imaginary.append(col)
data = data.drop(columns=imaginary)

print("Making feature level split graphs")
def mean_for_single_feature_graph(feature):
    data_learning = pd.concat([data.reset_index(drop=True), feat_csv.reset_index(drop=True)],axis=1)

    dist5 = (DISTANCE / 5) #make the increments flex with distance
    incrementor = 0 

    df_list = []

    data_learning = data_learning.filter(like=feature)
    
    while incrementor < DISTANCE:
        incrementor += dist5

        tmp = data_learning[data_learning[feature] <= incrementor]
        tmp = tmp.sort_values(by=[feature])
        df_list.append(tmp)
    
        data_learning = data_learning[data_learning[feature] > incrementor]

    _, axes = plt.subplots(5 ,1, figsize=(10, 3 * ORDER))
    count = 0
    for df in df_list:
        df = df.drop(columns=[feature])
        part_mean = df.mean(axis=1)

        theta = np.linspace(0, THETA_MAX, len(part_mean))
        std = df.std(axis=1)
        axes[count].set_title(f"Mean distribution of {feature} - Level {levels[count]} - {LABEL_COL}")
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
        
#for feature in features:
    #mean_for_single_feature_graph(feature=feature)

print("Making feature order split graphs")
def interpolate_dense(theta, y, factor=100):
    theta_dense = np.linspace(theta[0], theta[-1], len(theta) * factor)
    cs = CubicSpline(theta, y)
    return theta_dense, cs(theta_dense)
""" NOTE: This does not work due to how the FEATHER Data is cunstrocted
def Split_on_order(feature, eval_points=10):
    data_feature = data.filter(like=feature)

    _, axes = plt.subplots(ORDER, 1, figsize=(10, 5 * ORDER))
    for o in range(ORDER):
        start = int((o * eval_points))
        end = int(((o+1) *eval_points))

        data_subset = data_feature.iloc[:,start:end]
        data_subset = pd.concat([data_subset, feat_csv.filter(like=feature)], ignore_index=False, axis=1)

        sorted_data = data_subset.sort_values(by=[feature])
        sorted_data = sorted_data.drop(columns=[feature])

        part_mean = sorted_data.mean(axis=1) 
        std = sorted_data.std(axis=1) 

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

for feature in features:
    Split_on_order(feature)
"""
def percentage_split_graph():
    new_data = pd.concat([data, feat_csv], ignore_index=False, axis=1)
    new_data['mean'] = feat_csv.mean(axis=1)
    sorted_data = new_data.sort_values('mean')

    long = sorted_data.shape[0]

    sorted_data = sorted_data.drop(columns=features)

    sorted_data = sorted_data.drop(columns=['mean'])

    df_bottom = sorted_data.head(int(long * 0.25))
    df_high = sorted_data.tail(int(long * 0.25))

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
            
    ax.plot(theta_smooth, high_smooth, color='blue', label='Top 25%')
    ax.fill_between(theta_smooth, high_smooth - high_std_smooth, high_smooth + high_std_smooth, color='blue', alpha=0.4)
    ax.set_xlim(0, THETA_MAX)
    ax.set_xlabel(r'Evaluation point: $\theta$')     
    ax.set_ylabel("CF Value")
    ax.set_ylim(-1.1,1.1) 
    ax.set_title(f"mean distribution for 25% highest and lowest scoring nodes - {LABEL_COL}")

    ax.plot(theta_smooth, low_smooth, color='red', label='Bottom 25%')
    ax.fill_between(theta_smooth, low_smooth - std_low_smooth, low_smooth + std_low_smooth, color='red', alpha=0.4)
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT + f"percentage")

print("Making percentage graphs")
#percentage_split_graph()

def percentage_split_graph_split():
    new_data = pd.concat([data, feat_csv], ignore_index=False, axis=1)
    new_data['mean'] = feat_csv.mean(axis=1)
    sorted_data = new_data.sort_values('mean')

    long = sorted_data.shape[0]

    sorted_data = sorted_data.drop(columns=features)

    sorted_data = sorted_data.drop(columns=['mean'])

    df_bottom = sorted_data.head(int(long * 0.25))
    df_high = sorted_data.tail(int(long * 0.25))

    mean_high = df_high.mean(axis=1).values   
    mean_low  = df_bottom.mean(axis=1).values
    std_high  = df_high.std(axis=1).values
    std_low   = df_bottom.std(axis=1).values
                            
    theta = np.linspace(0, THETA_MAX, len(mean_high))
    
    theta_smooth, high_smooth = interpolate_dense(theta, mean_high, factor=100)
    _, low_smooth = interpolate_dense(theta, mean_low, factor=100)
    _, std_low_smooth = interpolate_dense(theta, std_low, factor=100)
    _, high_std_smooth = interpolate_dense(theta, std_high, factor=100)
    
    _, ax = plt.subplots(2,figsize=(18, 12))
            
    ax[0].plot(theta_smooth, high_smooth, color='blue', label='Top 25%')
    ax[0].fill_between(theta_smooth, high_smooth - high_std_smooth, high_smooth + high_std_smooth, color='blue', alpha=0.4)
    ax[0].set_xlim(0, THETA_MAX)
    ax[0].set_xlabel(r'Evaluation point: $\theta$')     
    ax[0].set_ylabel("CF Value")
    ax[0].set_ylim(-1.1,1.1) 
    ax[0].set_title(f"mean distribution for 25% highest scoring nodes - {LABEL_COL}")
    ax[0].legend()

    ax[1].plot(theta_smooth, low_smooth, color='red', label='Bottom 25%')
    ax[1].fill_between(theta_smooth, low_smooth - std_low_smooth, low_smooth + std_low_smooth, color='red', alpha=0.4)
    ax[1].set_xlim(0, THETA_MAX)
    ax[1].set_xlabel(r'Evaluation point: $\theta$')     
    ax[1].set_ylabel("CF Value")
    ax[1].set_ylim(-1.1,1.1) 
    ax[1].set_title(f"mean distribution for 25% lowest scoring nodes - {LABEL_COL}")
    ax[1].legend()

    plt.tight_layout()
    plt.savefig(OUTPUT + f"percentage_split")

#percentage_split_graph_split()

