import json
from datetime import date as Date, timedelta as TimeDelta
from typing import Tuple, Sequence, Mapping, Union, Optional, List
import pandas as pd
from pandas import Timestamp as TS
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session
from toolz import compose, pipe, juxt, first, last, curry
from toolz.curried import get, groupby
from toolz.curried import map  # pylint: disable=redefined-builtin

# TO DO: refresh tokens
# TO DO: fix cache merging
# TO DO: clean data (remove naps, etc)
# TO DO: paginate requests

DEBUG = True
if DEBUG:
    from pdb import pm  # pylint: disable=unused-import,no-name-in-module


# Mapping is actually "RawDateData" but recursive types not supported yet
RawDateData = Mapping[str, Union[str, Mapping]]
RawData = List[RawDateData]


# helper functions for parsing the fitbit API response
# these are pure


def start_ts_parsed_from_raw_data(raw_data: RawDateData) -> TS:
    if isinstance(raw_data["startTime"], str):
        return TS(raw_data["startTime"])
    raise Exception("malformed data")


def start_date_parsed_from_raw_data(raw_data: RawDateData) -> Date:
    ts = start_ts_parsed_from_raw_data(raw_data)
    # the date might need to be corrected
    return ts.date() - TimeDelta(0 if ts.hour > 18 else 1)


ROOT_FIELDS = ["timeInBed", "minutesAsleep", "efficiency"]
LEVELS_FIELDS = ["wake", "light", "deep", "rem"]
HEADER = ["date", "startTime"] + ROOT_FIELDS + LEVELS_FIELDS

parsed_levels = [
    compose(get("minutes"), level_getter, get("summary"), get("levels"))
    for level_getter in map(get(default={"minutes": 0}), LEVELS_FIELDS)
]
parsed_body = juxt(
    start_date_parsed_from_raw_data,
    start_ts_parsed_from_raw_data,
    *map(get, ROOT_FIELDS),
    *parsed_levels,
)


def parsed_data(raw_data: RawData) -> pd.DataFrame:
    parsed = map(parsed_body, raw_data)
    data = pd.DataFrame(parsed)
    if len(data.columns) != len(HEADER):
        breakpoint()
    data.columns = HEADER
    data.index = pd.to_datetime(data.date)
    return data


class Fitbit:
    session: Optional[OAuth2Session] = None

    def __init__(self) -> None:
        try:
            self.cache = pd.read_csv("sleep.csv")
            self.cache.index = pd.to_datetime(self.cache.date)
        except FileNotFoundError:
            self.cache = pd.DataFrame(columns=HEADER)

    def auth(self) -> None:
        if self.session is not None:
            return
        client = MobileApplicationClient(client_id="22DGXL")
        self.session = OAuth2Session(client=client, scope=["sleep"])
        try:
            self.session.token = json.load(open(".fitbit-token"))
        except IOError:
            auth_base = "https://www.fitbit.com/oauth2/authorize"
            expiry = "31536000"
            auth_url = self.session.authorization_url(auth_base, expires_in=expiry)[0]
            print(f"Visit this page in your browser: \n{auth_url}")
            callback_url = input("Paste URL you get back here: ")
            self.session.token_from_fragment(callback_url)
            json.dump(self.session.token, open(".fitbit-token", "w"))

    # this is unsafe
    def fetch_raw_data_for_range(self, date_range: Tuple[str, str]) -> RawData:
        self.auth()
        url = "https://api.fitbit.com/1.2/user/-/sleep/date/{}/{}.json".format(
            *date_range
        )
        # doesn't include the last date!
        response = self.session.get(url)  # type: ignore
        if not response.ok:
            print(response.json())
        result: RawData = response.json()["sleep"]
        return result

    def get_data(
        self, start_str: str, stop_str: str, fetch: bool = True, fill: bool = False
    ) -> pd.Series:
        if not fetch:
            return self.cache.iloc[
                (self.cache.index >= TS(start_str)) & (self.cache.index < TS(stop_str))
            ]
        # date_range includes the last date, but the fitbit API doesn't
        requested_dates: Sequence[TS] = pd.date_range(start_str, stop_str)
        # don't check the cache for the last one!
        needed_dates = sorted(list(set(requested_dates[:-1]) - set(self.cache.index)))
        needed_ranges = find_ranges(needed_dates)

        def collect_data(date_range: Tuple[Date, Date]) -> pd.DataFrame:
            str_range: Tuple[str, str] = tuple(map(Date.isoformat, date_range))
            raw_data = self.fetch_raw_data_for_range(str_range)
            new_data = parsed_data(raw_data)  # add nap filtering here
            return new_data

        collected_df = pd.concat(map(collect_data, needed_ranges))
        if fill:
            missing_dates = set(needed_dates) - set(collected_df.index)
            row_fill = [None] * len(HEADER[1:])
            matrix_fill = [([date] + row_fill) for date in missing_dates]
            df_fill = pd.DataFrame(matrix_fill, columns=HEADER, index=missing_dates)
            collected_df = pd.concat([collected_df, df_fill])
        self.cache = pd.concat(
            [self.cache, collected_df], sort=False
        ).sort_index()
        self.cache.to_csv("sleep.csv")
        return self.cache[requested_dates[0] : requested_dates[-1]]


# these are also pure
# helper functions for deciding what ranges to query for
def offset_between_index_and_ts(index_and_ts: Tuple[int, TS]) -> int:
    index, ts = index_and_ts
    return index - ts.date().toordinal()


def find_ranges(seq: Sequence[TS]) -> Sequence[Tuple[TS, TS]]:
    # consecutive dates have the same offset from their index
    ranges = pipe(
        seq,
        enumerate,  # -> Iterator[Tuple[int, TS]]
        groupby(offset_between_index_and_ts),  # -> Dict[int, List[Tuple[int, TS]]]
        dict.values,  # -> Iterator[List[Tuple[int, TS]]]
        map(map(last)),  # -> Iterator[Iterator[TS]]
        map(list),  # -> Iterator[List[TS]]
        map(juxt(first, last)),  # -> Iterator[Tuple[Ts, Ts]]
        list,  # -> List[Tuple[Ts,Ts]]
    )
    return ranges


fitbit = Fitbit()
get_data = fitbit.get_data
