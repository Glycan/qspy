from pdb import pm
from itertools import zip_longest
from typing import Tuple, Iterator
import pandas as pd
from pandas import Timestamp as TS
from dateutil.parser import parse as parse_dt
from toolz import curry, pipe, valmap
from toolz.curried import map, drop  # pylint: disable=redefined-builtin
from scipy.stats import ttest_ind
from statsmodels.stats.power import TTestIndPower
import fitbit

# import sheets

def find_sleep_times(log: pd.DataFrame) -> pd.Series:
    dup_ts = pd.DataFrame({"content": log["content"], "ts": log.index})
    all_sleeps = dup_ts[log["content"] == "sleep"]
    # in the evening, this rounds to the next day (so we substract it to the correct bedtime day)
    # we want to consider early morning as the previous day, early morning rounds to the same day
    # so substracting gives us the day we want
    day_groups = all_sleeps.groupby(lambda ts: ts.round("D") - pd.Timedelta("1D"))
    sleep_times = day_groups.last()["ts"]
    return sleep_times


if __name__ == "__main__":
    sleep = fitbit.get_data("2019-03-22", "2019-04-27")
    data: Iterator[Tuple[str]] = pipe(
        open("data/modafinil-data"),
        map(curry(str.split)(maxsplit=3)),
        lambda rows: zip_longest(*rows, fillvalue=""),
    )
    dates = pipe(next(data), map(parse_dt), map(TS), pd.Series)
    parsed_data = {
        "number": pipe(next(data), map(drop(1)), map("".join), map(float)),
        "treatment": map("A".__eq__, next(data)),
        "times": next(data),
    }
    modafinil_df = pd.DataFrame(valmap(curry(pd.Series, index=dates), parsed_data))
    new_sleep = sleep.copy()

    merged = new_sleep.merge(modafinil_df, right_index=True, left_index=True)
    treated = merged[merged.treatment].efficiency
    untreated = merged[~merged.treatment].efficiency
    p_val = ttest_ind(treated, untreated)
    mean_diff = (
        sum(treated) / len(treated) - sum(untreated) / len(untreated)
    ) / merged.efficiency.std()
    # now get this to actualy work and abstract it so it works with arbitrary columns, depression, etc
    num = TTestIndPower().solve_power(0.8, power=0.95, nobs1=None, alpha=0.2)
