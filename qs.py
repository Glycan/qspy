from pdb import pm
import fitbit
import sheets
import pandas as pd




#sleep = fitbit.get_data("2019-04-01", "2019-05-01")
#sleep = fitbit.get_data("2019-04-01", "2019-04-17")


log = pd.DataFrame(sheets.get_data())
import pdb
pdb.set_trace()
# you want to *not* use a series, but a dataframe with the ts, in order to have group keys that are dates and then select the ts for the sleep time
sleep_starts = log[log.content == "sleep"].groupby(lambda ts: ts.floor("D")).last().index

