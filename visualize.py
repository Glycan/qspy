import matplotlib.pyplot as plt
import os



def plot_field(data, field="efficiency", title="sleep efficiency over time"):
    plt.ylabel(field)
    plt.title(title)
    data[field].plot()
    cwd = os.getcwd()
    os.chdir("../public_html")
    plt.savefig("{}.png".format(field))
    os.chdir(cwd)

