#import os
import json
import csv
#import sys
from typing import List, Tuple
from itertools import groupby
from datetime import datetime, date, timedelta
from pdb import pm, set_trace
from oauthlib.oauth2 import MobileApplicationClient # BackendApplicationClient
import pandas as pd
from pandas import Timestamp as Ts
from requests_oauthlib import OAuth2Session

import pdb
DEBUG = True

# TODO: refresh tokens
# TODO: fix cache merging

# TODO: clean data (remove naps, etc)
# TODO: paginate requests





# helper functions for parsing the fitbit API response

def parse_starttime(day: str) -> datetime:
    return datetime.strptime(day["startTime"], "%Y-%m-%dT%H:%M:%S.%f")

def decide_date(day: str) -> datetime.date:
    dt = parse_starttime(day)
    return dt.date() - timedelta(0 if dt.hour > 18 else 1)

# helper functions for deciding what ranges to query for

def first_last(enumerated_dates: List[Tuple[int, Ts]]) -> Tuple[Ts, Ts]:
    enumerated_dates = list(enumerated_dates)
    return (enumerated_dates[0][1], enumerated_dates[-1][1])

def find_ranges(seq):
    # consecutive dates have the same offset from their index
    groups = groupby(
        enumerate(seq),
        lambda enumerated_date: (
            enumerated_date[0]
            - enumerated_date[1].toordinal()
        )
    )
    ranges = [
        first_last(enumerated_group)
        for key, enumerated_group in groups
    ]
    return ranges


class Fitbit:
    columns = {
        "date": decide_date,
        "startTime": parse_starttime,
        **{
            field: lambda day: day[field]
            for field in ["timeInBed", "minutesAsleep", "efficiency"]
        },
        **{
            field: lambda day: (
                "n/a"
                if day["type"] == "classic"
                else day["levels"]["summary"][field]["minutes"]
            )
            for field in ["wake", "light", "deep", "rem"]
        }
    }
    header, parsers = zip(*columns.items())

    def __init__(self):
        #client_secret = "c3c6a8b42eb609e5fca02842f4b0bd01"
        client = MobileApplicationClient(client_id="22DGXL")
        self.session = OAuth2Session(client=client, scope=["sleep"])
        try:
            token = json.load(open(".fitbit-token"))
            self.session.token = token
        except IOError:
            authorization_url = "https://www.fitbit.com/oauth2/authorize"
            auth_url = self.session.authorization_url(
                authorization_url,
                expires_in="31536000"
            )[0]
            print("Visit this page in your browser: \n{}".format(auth_url))
            callback_url = input("Paste URL you get back here: ")
            self.session.token_from_fragment(callback_url)
            token = self.sesion.token
            json.dump(token, open(".fitbit-token", "w"))
        try:
            self.cache = pd.read_csv("sleep.csv")
            self.cache.index = pd.to_datetime(self.cache.date)
        except FileNotFoundError:
            self.cache = pd.DataFrame(columns=self.header)

    def scrape_data(self, data):
        output = pd.DataFrame([
            [parse(day) for parse in self.parsers]
            for day in data
        ])
        output.columns = self.header
        output.index = pd.to_datetime(output.date)
        return output

    def fetch_range(self, start_date, stop_date, raw=False):
        response = self.session.get(
            "https://api.fitbit.com/1.2/user/-/sleep/date/{}/{}.json".format(
                start_date,
                stop_date
            )
        ) # doesn't include the last
        if not response.ok:
            print(response.json())
        result = response.json()["sleep"]
        if raw:
            return result
        else:
            return self.scrape_data(result)           

#    def fetch_range(self, st, sto):
#        return pd.DataFrame([], columns=self.header)

    def get_data(self, start, stop):
        requested_days = pd.date_range(start, stop)
        # date_range includes the last date, but the fitbit API doesn't
        needed_days = sorted(list(set(requested_days[:-1]) - set(self.cache.index)))
        # don't check the cache for the last one!
        needed_ranges = find_ranges(needed_days)
        collected_data = pd.DataFrame(columns=self.header)
        for date_range in needed_ranges:
            if DEBUG:
                print("getting {} to {}".format(*date_range))
            collected_data = collected_data.merge(
                self.fetch_range(*map(date.isoformat, date_range))
            )
        self.cache = pd.merge_ordered(
            self.cache,
            collected_data,
            left_by="index",
            fill_method="ffil"
        )
        """
        missing_days = set(requested_days[:-1]) - set(self.cache.index)
        missing_data = pd.DataFrame(
            [
                ([day] + [None] * len(self.header[1:]))
                for day in missing_days
            ],
            columns = self.header
        )
        """
        self.cache = self.cache.merge(missing_data, how="outer")
        self.cache.to_csv("sleep.csv")
        pdb.set_trace()
        return self.cache[start:stop]

fitbit = Fitbit()
get_data = fitbit.get_data
