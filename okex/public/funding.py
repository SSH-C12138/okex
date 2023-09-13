from okex.api.publicApi import PublicAPI
import datetime, time, pytz, os
import cr_assis.account.consts as c
import numpy as np
import pandas as pd

class Funding(object):
    
    def __init__(self) -> None:
        self.api = PublicAPI()
        self.now_ts = int(time.time() * 1000)
        self.tz = pytz.UTC
        self.coin_price = {}
        self.tier: dict[str, list] = {}
        self.tickers:dict[str, dict] = {}
        self.instruments:dict[str, dict] = {}
        self.spreads: dict[str, pd.DataFrame] = {}
        self.csv_time_str = c.TIME_MILLISECONDS
        self.datacenter = os.path.expanduser("~")+f"/data/account/okex" if not os.path.exists(c.CENTER_PATH) else c.CENTER_PATH
        self.depth_path = os.path.expanduser("~")+f"/data/depthData" if not os.path.exists(c.DEPTH_PATH) else c.DEPTH_PATH
    
    def get_utc_time(self, days=0, seconds=0, microseconds=0,
                milliseconds=0, minutes=0, hours=0, weeks=0) -> datetime.datetime:
        return datetime.datetime.now().astimezone(self.tz) + datetime.timedelta(days=days, seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)
    
    def read_day_csv(self, path: str, start: datetime.datetime, end: datetime.datetime) -> pd.DataFrame:
        date, all_data = start, {}
        while date <= end:
            all_data[date.date()] = pd.read_csv(f"{path}/{date.date()}.csv") if os.path.isfile(f"{path}/{date.date()}.csv") else pd.DataFrame(columns = ["time"])
            date += datetime.timedelta(days = 1)
        ret = pd.concat(all_data.values()).sort_values(by = "time")
        ret["time"] = ret["time"].apply(lambda x: datetime.datetime.strptime(x, self.csv_time_str).replace(tzinfo = self.tz))
        return ret[(ret["time"] >= start) & (ret["time"] <= end)].reset_index(drop=True)
    
    def get_depthData(self, instId: str, start:datetime.datetime = datetime.datetime.now().astimezone(pytz.UTC) + datetime.timedelta(days = -1), end:datetime.datetime = datetime.datetime.now().astimezone(pytz.UTC)) -> pd.DataFrame: 
        """
        Args:
            instId (str): the instId 
            start (datetime.datetime, optional): _description_. Defaults to datetime.datetime.now().astimezone(pytz.tz)+datetime.timedelta(days = -1).
            end (datetime.datetime, optional): _description_. Defaults to datetime.datetime.now().astimezone(pytz.tz).
        Returns:
            pd.DataFrame: _description_
        """
        pair = instId.lower().replace("-", "_")
        kind = pair.split("_")[-1] if not str.isnumeric(pair.split("_")[-1]) else "delivery"
        data = self.read_day_csv(path = f"{self.depth_path}/{kind}/{pair}", start=start, end = end)
        return data if len(data) > 0 else pd.DataFrame(columns = ["bid", "bidVol","ask", "askVol","time"])
    
    def get_spreadData(self, combo: str, start:datetime.datetime = datetime.datetime.now().astimezone(pytz.UTC) + datetime.timedelta(days = -1), end:datetime.datetime = datetime.datetime.now().astimezone(pytz.UTC)) -> pd.DataFrame:
        self.depthData = {c.MASTER: self.get_depthData(instId=combo.split("-")[0], start = start, end = end), c.SLAVE: self.get_depthData(instId=combo.split("-")[-1], start = start, end = end)}
        data = pd.merge(self.depthData[c.MASTER][["bid", "ask", "time"]].rename(columns={"bid": f"{c.MASTER}_bid", "ask": f"{c.MASTER}_ask"}), self.depthData[c.SLAVE][["bid", "ask", "time"]].rename(columns={"bid": f"{c.SLAVE}_bid", "ask": f"{c.SLAVE}_ask"}), on = "time")
        self.spreadData = pd.DataFrame(columns = [c.LONG, c.SHORT, "time"]).astype({c.LONG: "float64", c.SHORT: "float64", "time": "datetime64[ns]"})
        self.spreadData[c.LONG], self.spreadData[c.SHORT], self.spreadData["time"] = data[f"{c.SLAVE}_bid"]/data[f"{c.MASTER}_bid"], data[f"{c.MASTER}_ask"]/data[f"{c.SLAVE}_ask"], data["time"]
        self.spreads[combo] = self.spreadData.copy()
        return self.spreadData
    
    def get_spread(self, combo: str, start:datetime.datetime = datetime.datetime.now().astimezone(pytz.UTC) + datetime.timedelta(days = -1), end:datetime.datetime = datetime.datetime.now().astimezone(pytz.UTC)) -> pd.DataFrame:
        return self.spreads[combo] if combo in self.spreads.keys() else self.get_spreadData(combo, start, end)
    
    def dt_to_ts(self, dt: datetime.datetime) -> int:
        return int(datetime.datetime.timestamp(dt.replace(tzinfo=self.tz)) * 1000)

    def get_discount_info(self, coin: str) -> list:
        if not hasattr(self, "discount_info"):
            response = self.api.discount_interest_free_quota()
            ret = response.json()["data"] if response.status_code == 200 else []
            self.discount_info = {info["ccy"]: info for info in ret}
        return self.discount_info[coin.upper()]['discountInfo'] if coin.upper() in self.discount_info.keys() and 'discountInfo' in self.discount_info[coin.upper()].keys() else []

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
    
    def organize_type_instruments(self, instType: str) -> None:
        ret = self.get_type_instruments(instType=instType)
        self.instruments.update({i["instId"]: i for i in ret})
    
    def get_contractsize(self, instId: str) -> float:
        instType = self.get_instType(instId)
        if instType == "SPOT":
            return 1
        elif instType == "SWAP":
            return self.get_contractsize_swap(instId)
        else:
            return np.nan
    
    def get_contractsize_swap(self, instId: str) -> float:
        instId = instId.upper()
        self.organize_type_instruments(instType="SWAP") if instId not in self.instruments.keys() else None
        if instId in self.instruments.keys():
            ret = float(self.instruments[instId]["ctVal"])
        else:
            ret, self.instruments[instId] = np.nan, {"ctVal": "nan"}
        return ret
    
    def get_contractsize_cswap(self, coin: str) -> float:
        return self.get_contractsize_swap(instId=f"{coin.upper()}-USD-SWAP")
    
    def get_contractsize_uswap(self, coin: str) -> float:
        return self.get_contractsize_swap(instId=f"{coin.upper()}-USDT-SWAP")
    
    def get_contractsize_usdc(self, coin: str) -> float:
        return self.get_contractsize_swap(instId=f"{coin.upper()}-USDC-SWAP")
    
    def get_tier_swapAPI(self, instId: str) -> list:
        response = self.api.get_tier(instType = "SWAP", tdMode = "cross", instFamily=instId.upper().replace("_", "-").replace("-SWAP", ""))
        ret = response.json()["data"] if response.status_code == 200 else []
        return ret
    
    def get_tier_spotAPI(self, coin: str) -> list:
        response = self.api.get_tier(instType = "MARGIN", tdMode = "cross", ccy = coin.upper().replace("_", "-").split("-")[0])
        ret = response.json()["data"] if response.status_code == 200 else []
        return ret
    
    def get_tier_swap(self, instId: str) -> list:
        instId = instId.upper().replace("_", "-")
        if os.path.isfile(f"""{os.path.expanduser("~")}/data/tier/okex/{instId}.csv"""):
            tier = pd.read_csv(f"""{os.path.expanduser("~")}/data/tier/okex/{instId}.csv""").to_dict('records')
        else:
            tier = self.get_tier_swapAPI(instId=instId)
        self.tier.update({instId: tier})
        return tier
    
    def get_tier_spot(self, coin: str) -> list:
        coin = coin.upper().replace("_", "-").split("-")[0]
        if os.path.isfile(f"""{os.path.expanduser("~")}/data/tier/okex/{coin}.csv"""):
            tier =  pd.read_csv(f"""{os.path.expanduser("~")}/data/tier/okex/{coin}.csv""").to_dict('records')
        else:
            tier =  self.get_tier_spotAPI(coin=coin)
        self.tier.update({coin: tier})
        return tier
    
    def get_mmr_spot(self, coin: str, amount: float) -> float:
        """get mmr of spot

        Args:
            coin (str): the name of coin, str.upper()
            amount (float): the coin number of spot asset, not dollar value
        """
        coin = coin.upper()
        tier = self.tier[coin] if coin in self.tier.keys() else self.get_tier_spot(coin)
        mmr = self.find_mmr(amount = amount, tier = tier)
        return mmr
    
    def get_mmr_swap(self, instId: str, amount: float) -> float:
        """get mmr of swap contract

        Args:
            coin (str): the name of coin, str.upper()
            amount (float): the contract number of swap, not dollar value, not coin number
        """
        instId = instId.upper().replace("_", "-")
        tier = self.tier[instId] if instId in self.tier.keys() else self.get_tier_swap(instId)
        mmr = self.find_mmr(amount = amount, tier = tier)
        return mmr
    
    def get_mmr(self, instId: str, amount: float) -> float:
        coin, instType = instId.upper().replace("_", "-").split("-")[0], self.get_instType(instId=instId)
        if instType == "SPOT":
            mmr = 0 if amount >=0 else self.get_mmr_spot(coin, -amount)
        elif instType == "SWAP":
            mmr = self.get_mmr_swap(instId.upper().replace("_", "-"), abs(amount))
        else:
            mmr = np.nan
        return mmr
    
    def find_mmr(self, amount: float, tier: list) -> float:
        """
        Args:
            amount (float): the amount of spot asset or swap contract
            tier (pd.DataFrame): the position tier information
        """
        if amount <= 0:
            return 0
        else:
            mmr = np.nan
            for info in tier:
                if amount > float(info["minSz"]) and amount <= float(info["maxSz"]):
                    mmr = float(info["mmr"])
                    break
            return mmr
    
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
    
    def update_coin_price(self) -> None:
        self.get_tickers(instType= "SPOT")
        self.coin_price.update({instId.split("-")[0].upper(): float(info["last"]) for instId, info in self.tickers.items() if (info["instId"].split("-")[1]=="USDT" and info["instType"] != "FUTURES")})
            
    def get_coin_price(self, coin: str) -> float:
        coin = coin.upper()
        self.update_coin_price() if coin not in self.coin_price.keys() else None
        if coin in self.coin_price.keys():
            ret = self.coin_price[coin]
        else:
            ret, self.coin_price[coin] = np.nan, np.nan
        return ret
    
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
    
    def get_price(self, instId: str) -> float:
        instId, instType = instId.upper(), self.get_instType(instId)
        self.get_tickers(instType=instType) if instId not in self.tickers.keys() else None
        return float(self.tickers[instId]["last"]) if instId in self.tickers.keys() else np.nan
    
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