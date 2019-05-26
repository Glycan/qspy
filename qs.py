from pdb import pm
import fitbit
import sheets
import pandas as pd
import matplotlib.pyplot as plt
import numpy as nd
import os

import pdb


# TODO: cache data
# google token length
# parse drug log

# clean sleep data (exclude naps, remove non-normal dates)

# TODO: paginate requests



LOG = "1IkWwtBNjwvoemWm9pdAO3Ni8sYvhRg_V-B5AHgpu9-8"

#sleep = fitbit.get_data("2019-04-01", "2019-05-01")
#sleep = fitbit.get_data("2019-04-01", "2019-04-17")

def plot_field(field="efficiency", title="sleep efficiency over time"):
    plt.ylabel(field)
    plt.title(title)
    sleep[field].plot()
    cwd = os.getcwd()
    os.chdir("../public_html")
    plt.savefig("{}.png".format(field))
    os.chdir(cwd)


#log = pd.DataFrame(sheets.get_data(LOG))


