import json
import pickle
import os.path
from typing import Optional
from datetime import date, datetime
import pandas as pd
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


# TODO: google token length
# TODO: parse drug log

LOG = "1IkWwtBNjwvoemWm9pdAO3Ni8sYvhRg_V-B5AHgpu9-8"


class Sheet:
    def __init__(self, sheet_id: Optional[str]=None):
        if sheet_id is None:
            self.sheet_id = LOG
        else:
            self.sheet_id = sheet_id
        self.spreadsheets = None
        try:
            self.cache = pd.read_csv("log.csv")
        except FileNotFoundError:
            self.cache = pd.DataFrame()

    def auth(self):
        if self.spreadsheets is not None:
            return
        creds = None
        if os.path.exists("token.pickle"):
            with open("google-token.pickle", "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json",
                    ["https://www.googleapis.com/auth/spreadsheets.readonly"]
                )
                flow.redirect_uri = "https://localhost"
                authorization_url, state = flow.authorization_url()
                print("visit {}".format(authorization_url))
                flow.fetch_token(
                    authorization_response=input("paste redirect url: ")
                )
                creds = flow.credentials
            with open("google-token.pickle", "wb") as token:
                pickle.dump(creds, token)
        service = build("sheets", "v4", credentials=creds)
        self.spreadsheets = service.spreadsheets()

    def get_data(self, refresh: Optional[bool]=False) -> pd.DataFrame:
        if self.cache.empty or refresh:
            self.auth()
            result = pd.DataFrame(self.spreadsheets.values().get(
                spreadsheetId=self.sheet_id,
                range="log!A1:B2000"
            ).execute()["values"])
            if not result.empty:
                self.cache = result
                self.cache.to_csv("log.csv")
        return self.cache

sheets = Sheets()
get_data = sheets.get_data

