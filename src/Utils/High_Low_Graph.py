import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

CSV_FILE = "projects\Washington\FeatherResult.csv"
OUTPUT = "./projects/Washington/"
LABEL_COL = "Washington"
ORDER=5
THETA_MAX=2.5
DISTANCE = 2000

#Helper functions
"""splits dataframe into two parts, devied by the median of the mean."""
def split_dataframe(dataframe):
    decider = np.median(dataframe.mean(axis=0))

    dataframe["is_high_median"] = dataframe.mean(axis=1) > decider #Add this temporary column
    print(dataframe.mean(axis=1))
    print(dataframe["is_high_median"])

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

features = ["outdoor_activities","learning","supplies","eating","moving","cultural_activities","physical_exercise","services","healthcare","financial"]
color_arr = ["red", "blue", "green", "orange", "black", "yellow", "grey", "brown", "purple", "pink"]

#Drop imaginary columns

data = pd.read_csv(CSV_FILE)
data = data.drop(columns =['id'])

"""Drop imaginary columns, keeping only the "real" ones"""
imaginary = []
for col in data.columns:
    if "img" in col and col not in imaginary:
        imaginary.append(col)
data = data.drop(columns=imaginary)


"""count the number of features"""
unique_features = set()

for col in data.columns:
    pls = col.rsplit("_", 1) #rsplit splits from the right insted of the left. removes the numbers
    unique_features.add(pls[0])
    print(pls)

num_features = len(unique_features)
print(f"Counted features:  {num_features}")

"""Creates one graph, showing the characteristic function value distribution over theta, with all orders combined to 
give an overall view. There us no seperation of features, all features are included.
"""

"""
def combined_orders(eval_points=10):
    _, ax = plt.subplots(1, 1, figsize=(10, 10))

    for o in range(ORDER):
        #Separate into order amount of slices
        start = int((o * eval_points * num_features) //THETA_MAX)
        end = int(((o+1) *eval_points * num_features) //THETA_MAX)
        
        data_high, data_low = split_dataframe(data.iloc[:, start:end])
        #calculate means, std and median
        data_high_mean, data_low_mean = get_mean(data_high, data_low)
        data_high_std, data_low_std = get_std(data_high, data_low)
        
        theta = np.linspace(0, THETA_MAX, len(data_high_mean))

        #color and plot
        high = color_arr[2*o]
        low = color_arr[2*o+1]

        ax = High_low_plotter(o, data_high_mean, data_high_std, ax, theta, isHigh=True, color=high)
        ax = High_low_plotter(o, data_low_mean, data_low_std, ax, theta, isHigh=False, color=low)

    ax.set_title(f"{LABEL_COL} - Distribution across all orders")
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=4)  

    plt.tight_layout()
    #plt.show()
    plt.savefig(OUTPUT + "combinedHighLow.png")

#combined_orders()
"""
"""Creates multiple graphs showing the distribution of characteristic function values over theata, with all orders seperated, 
but no seperation of features"""

"""
def separate_orders(eval_points = 10):
    fig, axes = plt.subplots(ORDER, 1, figsize=(14, 5 * ORDER))

    for o in range(ORDER):
        start = int((o * eval_points * num_features) // THETA_MAX)
        end = int(((o+1) * eval_points * num_features) // THETA_MAX)

        data_high, data_low = split_dataframe(data.iloc[:, start:end])
        data_high_mean, data_low_mean = get_mean(data_high, data_low)
        data_high_std, data_low_std = get_std(data_high, data_low)

        theta = np.linspace(0, THETA_MAX, len(data_high_mean))

        axes[o] = High_low_plotter(o, data_high_mean, data_high_std, axes[o], theta, isHigh=True, color='blue')
        axes[o] = High_low_plotter(o, data_low_mean, data_low_std, axes[o], theta, isHigh=False, color='red')
        axes[o].set_title(f"Order: {o}")
        axes[o].legend(loc='center left', ncol=1, bbox_to_anchor=(1, 0.5))
    
    fig.suptitle(f"{LABEL_COL} - Distribution across separate orders")
    plt.tight_layout()
    fig.subplots_adjust(hspace=0.6, top=0.92)
    plt.savefig(OUTPUT + "separatedHighLow.png")

#separate_orders()"""

"""Creates multiple graphs showing the distribution of characteristic function values over theta, with all orders seperated, 
looking at one specified feature"""

"""
def feature_in_orders(feature, eval_points = 10):
    data_subset = data.filter(like=feature) 

    fig, axes = plt.subplots(ORDER, 1, figsize=(10, 5*ORDER))

    for o in range(ORDER):
        start = int((o * eval_points) // THETA_MAX) #We only have one feature, so no multiplication
        end = int(((o+1) * eval_points) // THETA_MAX)

        data_high, data_low = split_dataframe(data_subset.iloc[:, start:end])
        data_high_mean, data_low_mean = get_mean(data_high, data_low)
        data_high_std, data_low_std = get_std(data_high, data_low)

        theta = np.linspace(0, THETA_MAX, len(data_high_mean))

        axes[o] = High_low_plotter(o, data_high_mean, data_high_std, axes[o], theta, isHigh=True, color='blue')
        axes[o] = High_low_plotter(o, data_low_mean, data_low_std, axes[o], theta, isHigh=False, color='red')
        axes[o].set_title(f"Order: {o}")
        axes[o].legend(loc='center left', ncol=1, bbox_to_anchor=(1, 0.5))

    fig.suptitle(f"{LABEL_COL} - Distribution across separate orders {feature}")
    plt.tight_layout()

    fig.subplots_adjust(hspace=0.6, top=0.92)
    plt.savefig(OUTPUT + feature +"HighLow.png")


feature_in_orders("moving")

#NOTE: if you want to go through all features
"""
#for feature in features:
    #feature_in_orders(feature)
    


def teis_stuff_single(feature):
    cool = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

    data_learning = pd.concat([data, cool], ignore_index=False, axis=1)
    print(data_learning.columns)
    print(data_learning)

    dist5 = (DISTANCE / 5) #make the increments flex with distance
    incrementor = 0 

    df_list = []

    data_learning = data_learning.filter(like=feature)
    
    while incrementor < DISTANCE:
        incrementor += dist5
        print(incrementor)

        tmp = data_learning[data_learning[feature] <= incrementor]
        tmp = tmp.sort_values(by=[feature])
        df_list.append(tmp)
        #val = np.round((tmp.shape[0])*100,3)
        #print( incrementor , "m range percentage:", val)
        data_learning = data_learning[data_learning[feature] > incrementor]
        #print(f"data_learning:______  {data_learning}")


    print(f"final: {df_list}")
    print(len(df_list))
    _, axes = plt.subplots(5 ,1, figsize=(14, 5 * ORDER))
    count = 0
    for lst in df_list:
        print(lst)
        
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
    teis_stuff_single(feature=feature)

def teis_stuff_order(feature, eval_points=10):
    cool = pd.read_csv("./projects/" + LABEL_COL + "/featuresteis.csv")

    data_learning = pd.concat([data, cool], ignore_index=False, axis=1)

    dist5 = (DISTANCE / 5) #make the increments flex with distance
    incrementor = 0 

    df_list = []

    data_learning = data_learning.filter(like=feature)

    for o in range(ORDER):
        start = int((o * eval_points * num_features) //THETA_MAX)
        end = int(((o+1) *eval_points * num_features) //THETA_MAX)
    
    while incrementor < DISTANCE:
        incrementor += dist5
        print(incrementor)

        tmp = data_learning[data_learning[feature] <= incrementor]
        tmp = tmp.sort_values(by=[feature])
        df_list.append(tmp)
      
        data_learning = data_learning[data_learning[feature] > incrementor]


    print(f"final: {df_list}")
    print(len(df_list))
    _, axes = plt.subplots(5 ,1, figsize=(14, 5 * ORDER))
    count = 0
    for lst in df_list:
        print(lst)
        
        lst = lst.drop(columns=[feature])
        part_mean = lst.mean(axis=1)

        theta = np.linspace(0, THETA_MAX, len(part_mean))
        std = lst.std(axis=1)

        axes[count].plot(theta, part_mean, color=color_arr[count], label=f"mean for {feature} ")
        axes[count].fill_between(theta, part_mean - std, part_mean + std, color=color_arr[count], alpha=0.4)
        axes[count].legend()

        #axes[count].set_xlim(0, THETA_MAX)
        axes[count].set_xlabel(r'Evaluation point: $\theta$')     
        axes[count].set_ylabel("CF Value")
        axes[count].set_ylim(-1.1,1.1) 
        count +=1
    
    plt.tight_layout()
    plt.savefig(OUTPUT + f"{feature}meanwave")