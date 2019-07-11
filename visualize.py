import matplotlib.pyplot as plt
import os
from pandas import DataFrame as DF


def plot_field(
    data: DF, field: str = "efficiency", title: str = "sleep efficiency over time"
) -> None:
    plt.ylabel(field)
    plt.title(title)
    data[field].plot()
    cwd = os.getcwd()
    os.chdir("../public_html")
    plt.savefig("{}.png".format(field))
    os.chdir(cwd)
