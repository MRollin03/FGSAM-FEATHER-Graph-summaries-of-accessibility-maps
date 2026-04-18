import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CSV_FILE = "Utils\projects\Copenhagen3\FeatherResult.csv"
OUTPUT = "./projects/Copenhagen3/"
LABEL_COL = "København"
ORDER=5
THETA_MAX=2.5

features = ["outdoor_activities","learning","supplies","eating","moving","cultural_activities","physical_exercise","services","healthcare","financial"]

#Drop imaginary columns
def columns_drop(dataframe):
    imaginary = []
    for col in dataframe.columns:
        if 'img' in col and col not in imaginary:
            imaginary.append(col)
    
    return dataframe.drop(columns=imaginary)

data = pd.read_csv(CSV_FILE)
data = data.drop(columns =['id'])
data = columns_drop(data)

print(data)
print("________________________________________")

#count features
def count_features(dataframe):
    unique_features = set()

    for col in dataframe.columns:
        pls = col.rsplit("_", 1)
        unique_features.add(pls[0])
    
    print(f"Counted features:  {len(unique_features)}")
    return len(unique_features)

num_features = count_features(data)

#split dataframe
def split_dataframe(dataframe):
    decider = np.median(dataframe.mean(axis=0))

    dataframe["is_high"] = dataframe.mean(axis=1) > decider #Add this temporary column

    df_high = dataframe.loc[dataframe["is_high"] == True]
    df_low  = dataframe.loc[dataframe["is_high"] == False]

    #Remove it again
    df_high = df_high.drop(columns=["is_high"], errors='ignore')
    df_low = df_low.drop(columns=["is_high"], errors='ignore')

    return df_high, df_low

data_high, data_low = split_dataframe(data)

#get stds, means and medians
def get_mean(df_high, df_low):
    return df_high.mean(axis=0), df_low.mean(axis=0) 

def get_std(df_high, df_low):
    return df_high.std(axis=0), df_low.std(axis=0)

def get_median(df_high, df_low):
    return df_high.median(axis=0), df_low.median(axis=0)

#Plotting, removed median, can be readded later
def plotter(order, mean, std, ax, theta, isHigh, color, theta_max = 2.5):
    if(isHigh):
        ax.plot(theta, mean, color=color, label=f"High distribution order {order}")
        ax.fill_between(theta, mean - std, mean + std, color=color, alpha=0.4)
    else:
        ax.plot(theta, mean, color=color, label=f"Low distribution order {order}")
        ax.fill_between(theta, mean - std, mean + std, color=color, alpha=0.4)

    ax.set_xlim(0, theta_max)
    ax.set_xlabel(r'$\theta$')     
    ax.set_ylabel('Characteristic Function Value')
    ax.legend()  

    print("plotting")
    return ax

#makes one graph, with all orders combined, no seperation of features
def combined_orders(data, order, theta_max, eval_points):
    color_arr = plt.cm.tab20(np.linspace(0, 1, order*2)) #times 2 because we separate high and low
    _, ax = plt.subplots(1, 1, figsize=(10, 10))

    for i in range(order):
        #Separate into order amount of slices
        start = int((i * eval_points * num_features) //theta_max)
        end = int(((i+1) *eval_points * num_features) //theta_max)
        
        data_high, data_low = split_dataframe(data.iloc[:, start:end])
        #calculate means, std and median
        data_high_mean, data_low_mean = get_mean(data_high, data_low)
        data_high_std, data_low_std = get_std(data_high, data_low)
        data_high_median, data_low_median = get_median(data_high, data_low)
        #theta
        theta = np.linspace(0, THETA_MAX, len(data_high_mean))

        #plot
        high = color_arr[2 * i]
        low = color_arr[2 * i + 1]

        ax = plotter(i, data_high_mean, data_high_std, ax, theta, isHigh=True, color=high)
        ax = plotter(i, data_low_mean, data_low_std, ax, theta, isHigh=False, color=low)

    ax.set_title("Mean across all orders")

    plt.tight_layout()
    plt.show()
    #plt.savefig("./projects/Copenhagen3/plsall_combinedlow.png")

combined_orders(data, ORDER, THETA_MAX, 10)

#makes multiple graph, with all orders combined, no seperation of features
def separate_orders(data, eval_points):
    _, axes = plt.subplots(ORDER, 1, figsize=(10, 3 * ORDER), constrained_layout=True)

    for o in range(ORDER):
        ax = axes[o]
        start = int((o * eval_points * num_features) // THETA_MAX)
        end = int(((o+1) * eval_points * num_features) // THETA_MAX)

        data_high, data_low = split_dataframe(data.iloc[:, start:end])
        data_high_mean, data_low_mean = get_mean(data_high, data_low)
        data_high_std, data_low_std = get_std(data_high, data_low)

        theta = np.linspace(0, THETA_MAX, len(data_high_mean))

        ax = plotter(o, data_high_mean, data_high_std, ax, theta, isHigh=True, color='blue')
        ax = plotter(o, data_low_mean, data_low_std, ax, theta, isHigh=False, color='red')
        ax.set_title(f"Order: {o}")

    plt.show()

separate_orders(data, 10)

#Looks at one feature across all orders
def feature_in_orders(feature, data, eval_points):
    data_subset = data.filter(like=feature)
    _, ax = plt.subplots(ORDER, 1, figsize=(10, 8), constrained_layout=True)

    for o in range(ORDER):
        start = int((o * eval_points) // THETA_MAX) #We only have one feature
        end = int(((o+1) * eval_points) // THETA_MAX)

        data_high, data_low = split_dataframe(data_subset.iloc[:, start:end])
        data_high_mean, data_low_mean = get_mean(data_high, data_low)
        data_high_std, data_low_std = get_std(data_high, data_low)

        theta = np.linspace(0, THETA_MAX, len(data_high_mean))

        ax[o] = plotter(o, data_high_mean, data_high_std, ax[o], theta, isHigh=True, color='blue')
        ax[o] = plotter(o, data_low_mean, data_low_std, ax[o], theta, isHigh=False, color='red')
        ax[o].set_title(f"Order: {o} Feature: {feature}")

    plt.show()
feature_in_orders("financial", data, 10)

#NOTE: if you want to go through all features
"""
for feature in features:
    feature_in_orders(feature, data, 10)
    """