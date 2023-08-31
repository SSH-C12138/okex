from okex.api.publicApi import PublicAPI
import datetime, time, pytz
import numpy as np

class Funding(object):
    
    def __init__(self) -> None:
        self.api = PublicAPI()
        self.now_ts = int(time.time() * 1000)
        self.tz = pytz.UTC
        self.tickers:dict[str, dict] = {}
        
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
    
    def get_margin_coins(self) -> set[str]:
        ret = self.get_margin_instruments()
        return  set([i["baseCcy"] for i in ret if i["state"] == "live"]) | set(["USDT", "USDC"])
    
    def get_spot_instruments(self) -> list:
        self.spot_instruments = self.get_type_instruments(instType="SPOT")
        return self.spot_instruments
    
    def get_contract_coins(self, contract: str) -> list:
        coins = [name.split("-")[0] for name in self.get_contract_names(contract)]
        return coins
    
    def get_contract_names(self, contract: str) -> list:
        contract = contract.upper().replace("_", "-")
        ccy,instType = contract.split("-")[0], self.get_instType(contract)
        names = [info["instId"] for info in self.get_type_instruments(instType=instType) if (info["state"] == "live" and (info["instFamily"].split("-")[-1] == ccy or info["quoteCcy"] == ccy))]
        return names
    
    def get_eth2_staking(self, days = 30) -> list:
        response = self.api.get_eth2_staking(days = days)
        return response.json()["data"] if response.status_code == 200 else []
    
    def get_longTS_info(self, func, params: dict) -> list:
        ts = params["end_ts"]
        data = []
        while ts >= params["start_ts"]:
            response = func(params["input"], after=ts, before = params["start_ts"]-1000)
            if response.status_code == 200:
                ret = response.json()["data"]
                data += ret
                ts = int(ret[-1][params["timestamp"]]) if len(ret) > 0 else params["start_ts"]-1000
            elif response.status_code == 429:
                time.sleep(0.1)
            else:
                print(f"""{params["error"]} error: {response.json()}""")
                break
        return data
    
    def get_long_funding(self, instId: str, start_ts: int, end_ts:int) -> list:
        params = {"input": instId, "timestamp": "fundingTime", "error": "funding", "start_ts": start_ts, "end_ts": end_ts}
        data = self.get_longTS_info(self.api.funding_rate_history, params=params)
        return data
    
    def get_long_funding_dt(self, instId: str, start: datetime.datetime, end: datetime.datetime) -> list:
        start_ts, end_ts = self.dt_to_ts(start), self.dt_to_ts(end)
        return self.get_long_funding(instId=instId, start_ts=start_ts, end_ts= end_ts)
    
    def get_long_interest(self, ccy: str, start_ts: int, end_ts: int) -> list:
        params = {"input": ccy, "timestamp": "ts", "error": "interest", "start_ts": start_ts, "end_ts": end_ts}
        data = self.get_longTS_info(self.api.get_interest_history, params=params)
        return data
    
    def get_long_interest_dt(self, ccy: str, start: datetime.datetime, end: datetime.datetime) -> list:
        start_ts, end_ts = self.dt_to_ts(start), self.dt_to_ts(end)
        return self.get_long_interest(ccy=ccy, start_ts=start_ts, end_ts= end_ts)
    
    def get_tickers(self, instType: str) -> None:
        response = self.api.get_tickers(instType=instType)
        ret = response.json()["data"] if response.status_code == 200 else []
        self.tickers.update({i["instId"]: i for i in ret})
    
    def get_instType(self, instId: str) -> str:
        ret = instId.split("-")[-1].upper()
        if str.isnumeric(ret) or "FUTURE" in ret:
            ret = "FUTURES"
        elif ret == "SWAP":
            ret = ret
        else:
            ret = "SPOT"
        return ret
    
    def get_vol(self, instId: str) -> float:
        instId, instType = instId.upper(), self.get_instType(instId)
        self.get_tickers(instType=instType) if instId not in self.tickers.keys() else None
        info = self.tickers[instId] if instId in self.tickers.keys() else {"volCcy24h": np.nan, "last": np.nan}
        ret = float(info["volCcy24h"]) * float(info["last"]) if instType not in  ["SPOT", "MARGIN"] else float(info["volCcy24h"])
        return ret
    
    def get_current_funding(self, instId: str) -> dict[str, float]:
        if "SWAP" in instId.upper():
            response = self.api.get_funding_rate(instId=instId.upper())
            ret = response.json()["data"][0] if response.status_code == 200 else {'fundingRate': 'nan', 'nextFundingRate': 'nan'}
        else:
            ret = {'fundingRate': '0', 'nextFundingRate': '0'}
        return {"current": float(ret["fundingRate"]), "next": float(ret['nextFundingRate'])}

    def get_current_interest(self, ccy: str) -> float:
        response = self.api.get_interest(ccy)
        ret = response.json()["data"][0] if response.status_code == 200 else {'estRate': 'nan', "preRate": "nan"}
        return {"estRate": float(ret["estRate"]), "preRate": float(ret['preRate'])}