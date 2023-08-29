from okex.api.publicApi import PublicAPI
import datetime, time, pytz

class Funding(object):
    
    def __init__(self) -> None:
        self.api = PublicAPI()
        self.now_ts = int(time.time() * 1000)
        self.tz = pytz.UTC
        
    def dt_to_ts(self, dt: datetime.datetime) -> int:
        return int(datetime.datetime.timestamp(dt.replace(tzinfo=self.tz)) * 1000)

    def get_type_instruments(self, instType: str) -> list:
        response = self.api.get_instruments(instType=instType)
        ret = response.json()["data"] if response.status_code == 200 else []
        return ret
    
    def get_swap_instruments(self) -> list:
        self.swap_instruments = self.get_type_instruments(instType = "SWAP")
        return self.swap_instruments

    def get_margin_instruments(self) -> list:
        self.margin_instruments = self.get_type_instruments(instType="MARGIN")
        return self.margin_instruments
    
    def get_long_funding(self, instId: str, start_ts: int, end_ts:int) -> list:
        ts = end_ts
        data = []
        while ts > start_ts:
            response = self.api.funding_rate_history(instId=instId, after=ts, before = start_ts)
            if response.status_code == 200:
                ret = response.json()["data"]
                data += ret
                ts = int(ret[-1]["fundingTime"]) if len(ret) > 0 else start_ts
            elif response.status_code == 429:
                time.sleep(0.3)
            else:
                print(f"""funding error: {response.json()}""")
                break
        return data
    
    def get_long_funding_dt(self, instId: str, start: datetime.datetime, end: datetime.datetime) -> list:
        start_ts, end_ts = self.dt_to_ts(start), self.dt_to_ts(end)
        return self.get_long_funding(instId=instId, start_ts=start_ts, end_ts= end_ts)