from pdb import pm
from itertools import zip_longest
from typing import Tuple, Iterator, Sequence
from statistics import mean
import pandas as pd
from pandas import Timestamp as TS
from dateutil.parser import parse as parse_dt
from toolz import curry, pipe, compose, identity
from toolz.curried import map, drop  # pylint: disable=redefined-builtin
from toolz.sandbox import unzip as transpose
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


def test(data: Sequence[float], treatment: Sequence[bool]):
    treated = data[treatment].dropna()
    untreated = data[~treatment].dropna()
    pooled_std = (treated.std ** 2 + untreated.std ** 2) ** 0.5
    effect_size = (mean(treated.std) - mean(untreated.std)) / pooled_std
    nobs1 = len(treated)
    nobs2 = len(untreated)
    ratio = nobs2 / nobs1
    power_for_alpha = curry(TTestIndPower().power, effect_size, nobs1, ratio)
    return {
        "p": ttest_ind(treated, untreated).pvalue,
        "d": effect_size,
        "pooled sd": pooled_std,
        "treated sd": treated.std,
        "untreated sd": untreated.std,
        "power for p<.2": power_for_alpha(0.2),
        "power for p<.05": power_for_alpha(0.05),
    }


row_format = [
    compose(TS, parse_dt),
    compose(drop(1), "".join, float),
    "A".__eq__,
    identity,
]

def parsed_row(row):
    padded_row = row + [""] * (len(row_format) - len(row))
    return [func(cell) for func, cell in zip(row_format,  padded_row)]

@curry
def apply(func, arg):
    return func(arg)

@curry
def accept_one(func, *arg):
    return func(arg)

@curry
def accept_variadic(func, arg):
    return func(*arg)

def iter_pipe(data, *funcs):
    map(compose(map), funcs)
    compose(map, func)
    [compose(map, func) for func in funcs]
    apply(compose, [map, func])
    non_variadic(compose)
    compose_left(*funcs)(data)
    map(accept_one(compose), zip(repeat(map), funcs))


    
def modafinil() -> None:
    dates, _numbers, treatments, _times = pipe(
        open("data/modafinil-data"),
        map(curry(str.split)(maxsplit=3)), # list of rows
        map(curry(zip, row_format)), # Iteratable[Tuple[Callable, str]]
        map(map(variadic(apply))), # Iterable[Iterable[apply(*Tuple[Callable, str])]]
        # that is,  Iterable[Iterable[X]]



    )
    dates, _numbers, treatments, _times = pipe(
        open("data/modafinil-data"),
        map(curry(str.split)(maxsplit=3)),
        map(parsed_row),
        transpose,
    )
    return pd.Series(treatments, index=pd.DatetimeIndex(dates, name="dates"))


if __name__ == "__main__":
    sleep = fitbit.get_data("2019-03-22", "2019-04-27")
    modafinil_treatments = modafinil()
    summary = test(sleep.efficiency, modafinil_treatments)
    print("; ".join(map("{}={}".format, summary.items())))
