import json
import pickle
import os.path
from datetime import date, datetime
from typing import Optional, Any
import pandas as pd


# TODO: google token length
# TODO: parse drug log

LOG = "1IkWwtBNjwvoemWm9pdAO3Ni8sYvhRg_V-B5AHgpu9-8"


def read_log(fname: str) -> pd.DataFrame:
    return pd.read_csv(fname, converters={"ts": pd.Timestamp}, index_col="ts")


class Sheet:
    def __init__(self, sheet_id: str = ""):
        if sheet_id == "":
            self.sheet_id = LOG
        else:
            self.sheet_id = sheet_id
        try:
            self.cache = read_log("log.csv")
        except FileNotFoundError:
            self.cache = pd.DataFrame()
        self.spreadsheets: Any = None

    def auth(self) -> None:
        if self.spreadsheets is not None:
            return
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

        creds = None
        if os.path.exists("token.pickle"):
            with open("google-token.pickle", "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "../secrets/google_sheets_credentials.json",
                    ["https://www.googleapis.com/auth/spreadsheets.readonly"],
                )
                flow.redirect_uri = "https://localhost"
                authorization_url, state = flow.authorization_url()
                print("visit {}".format(authorization_url))
                flow.fetch_token(authorization_response=input("paste redirect url: "))
                creds = flow.credentials
            with open("google-token.pickle", "wb") as token:
                pickle.dump(creds, token)
        service = build("sheets", "v4", credentials=creds)
        self.spreadsheets = service.spreadsheets()

    def process_data(self, data: list) -> pd.DataFrame:
        scratch = pd.DataFrame(data)
        ts = pd.to_datetime(scratch[0])  # todo: check what columns google returns
        # df = pd.DataFrame({"content": scratch[1], "ts": ts}, index=ts)
        # don't understand why this ends up being full of NaN/NaT -- do they not have the same indexes?
        df = pd.DataFrame()
        df["content"] = scratch["content"]
        df.index = ts
        return df

    def get_data(self, refresh: Optional[bool] = False) -> pd.DataFrame:
        if self.cache.empty or refresh:
            self.auth()
            result = (
                self.spreadsheets.values()
                .get(spreadsheetId=self.sheet_id, range="log!A1:B2000")
                .execute()["values"]
            )
            if not result.empty:
                self.cache = self.process_data(result)
                self.cache.to_csv("log.csv")
        return self.cache


sheets = Sheet()
get_data = sheets.get_data
