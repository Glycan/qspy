import json
from functools import reduce
from itertools import groupby
from datetime import datetime, date, time, timedelta
from typing import Tuple, Sequence, TypeVar
import pandas as pd
from pandas import Timestamp as TS
from oauthlib.oauth2 import MobileApplicationClient
from requests_oauthlib import OAuth2Session

# TO DO: refresh tokens
# TO DO: fix cache merging
# TO DO: clean data (remove naps, etc)
# TO DO: paginate requests

DEBUG = True
if DEBUG:
    from pdb import pm  # pylint: disable=unused-import,no-name-in-module

X = TypeVar("X")

# helper functions for deciding what ranges to query for

def offset_between_index_and_ts(index_and_ts: tuple[int, TS]) -> int:
    index, ts = index_and_ts
    return index - ts.tooridnal() - index


def range_from_enumeration_iterable(enumeration_iterable: Iterator[Tuple[int, X]]) -> Tuple[X, X]:
    enumerated_dates = list(enumerated_dates_group)
    return (enumerated_dates[0][1], enumerated_dates[-1][1])

def find_ranges(seq: Sequence[TS]) -> Sequence[Tuple[TS, TS]]:
    # consecutive dates have the same offset from their index
    enumerated_seq: Iterator[int, Ts] = enumerate(seq)
    groups: Sequence[Tuple[int, Sequence[Ts]]] = groupby(
        enumerated_seq,
        key=offset_between_index_and_ts
    )
    ranges = [first_last(enumerated_group) for key, enumerated_group in groups]
    return ranges


# helper functions for parsing the fitbit API response


def parsed_start_timestamp_from_date_str(date_str: str) -> TS:
    return datetime.strptime(day["startTime"], "%Y-%m-%dT%H:%M:%S.%f").time()

def parsed_start_date_from_date_str(date_str: str) -> date:
    ts = parsed_state_timestamp_from_date_str(date_str)
    # the date might need to be corrected
    return dt.date() - timedelta(0 if dt.hour > 18 else 1)



class Fitbit:
    def __init__(self):
        # client_secret = "c3c6a8b42eb609e5fca02842f4b0bd01"
        client = MobileApplicationClient(client_id="22DGXL")
        self.session = OAuth2Session(client=client, scope=["sleep"])
        try:
            token = json.load(open(".fitbit-token"))
            self.session.token = token
        except IOError:
            authorization_url = "https://www.fitbit.com/oauth2/authorize"
            auth_url = self.session.authorization_url(
                authorization_url, expires_in="31536000"
            )[0]
            print("Visit this page in your browser: \n{}".format(auth_url))
            callback_url = input("Paste URL you get back here: ")
            self.session.token_from_fragment(callback_url)
            token = self.session.token
            json.dump(token, open(".fitbit-token", "w"))
        try:
            self.cache = pd.read_csv("sleep.csv")
            self.cache.index = pd.to_datetime(self.cache.date)
        except FileNotFoundError:
            self.cache = pd.DataFrame(columns=self.header)


    def fetch_raw_data_for_range(self, start_str: str, stop_str: str) -> Mapping:
        response = self.session.get(
            "https://api.fitbit.com/1.2/user/-/sleep/date/{}/{}.json".format(
                start_date, stop_date
            )
        )  # doesn't include the last date!
        if not response.ok:
            print(response.json())
        result: Mapping = response.json()["sleep"]
        return result

    # columns = {
    #     "date": decide_date,
    #     "startTime": parse_starttime,
    #     **{
    #         field: lambda day, _field=field: day[_field]
    #         for field in 
    #     },
    #     **{
    #         field: lambda day, _field=field: (
    #             "n/a"
    #             if day["type"] == "classic"
    #             else day["levels"]["summary"][_field]["minutes"]
    #         )
    #         for field in 
    #     },
    # }
    header, parsers = zip(*columns.items())
    root_fields = ["timeInBed", "minutesAsleep", "efficiency"]
    levels_fields = ["wake", "light", "deep", "rem"]
    header = ["date", "startTime"] + root_fields + levels_fields
#    parsers = ([parsed_date, starttime] + tuple()
        # lambda date_data, _field=field: day

    def scraped_data(self, data: Mapping) -> pd.DataFrame:
        output = pd.DataFrame([[parse(day) for parse in self.parsers] for day in data])
        output.columns = self.header
        output.index = pd.to_datetime(output.date)
        return output

    def fetch_data_for_range(self, *range_str: str):
        return self.scraped_data(self.fetch_raw_data_for_range(*range_str))


    def get_data(self, start_date_str: str, stop_date_str: str) -> pd.Series:
        # date_range includes the last date, but the fitbit API doesn't
        requested_dates: Sequence[TS] = pd.date_range(start_date_str, stop_date_str)
        # don't check the cache for the last one!
        needed_dates = sorted(list(set(requested_dates[:-1]) - set(self.cache.index)))
        needed_ranges = find_ranges(needed_dates)
        initial_header = pd.DataFrame(colmns=self.header)
        collected_df = reduce(
            lambda so_far, date_range: pd.merge_ordered(
                so_far,
                self.fetch_range(*map(date.isoformat, date_range)),
                left_by="index",
                fill_method="ffil"
            ),
            self.cache
        )

        missing_dates = set(needed_dates) - set(collected_data.index())
        missing_matrix: List[Tuple[Date, None, ...]
        missing_data = pd.DataFrame(
            [([date] + [None] * len(self.header[1:])) for date in missing_dates],
            columns=self.header,
        )
        missing_df = pd.DataFrame(missing_matrix, columns=self.header)

        self.cache: pd.DataFrame  = collected_data.merge(missing_data, how="outer")
        self.cache.to_csv("sleep.csv")
        breakpoint()
        return self.cache[start:stop]


fitbit = Fitbit()
get_data = fitbit.get_data
