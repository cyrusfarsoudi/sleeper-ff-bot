from .base_api import BaseApi

class State(BaseApi):
    def __init__(self):
        self._base_url = "https://api.sleeper.app/v1/state/nfl"
        self._state = self._call(self._base_url)

    def get_season_start_date(self):
        return self._state["season_start_date"]

    def get_season_start_year(self):
        return int(self.get_season_start_date().split("-")[0])

    def get_season_start_month(self):
        return int(self.get_season_start_date().split("-")[1])

    def get_season_start_day(self):
        return int(self.get_season_start_date().split("-")[2])
    