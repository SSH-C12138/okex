from .client import Client
from .consts import *
import time

class PublicAPI(Client):

    def __init__(self) -> None:
        super().__init__()

    # Get Instruments
    def get_instruments(self, instType, uly=None, instId=None):
        params = {'instType': instType, 'uly': uly, 'instId': instId}
        return self._requests(INSTRUMENT_INFO, params)

    # Get Delivery/Exercise History
    def get_deliver_history(self, instType, uly, after=None, before=None, limit=None):
        params = {'instType': instType, 'uly': uly, 'after': after, 'before': before, 'limit': limit}
        return self._requests(DELIVERY_EXERCISE, params)

    # Get Open Interest
    def get_open_interest(self, instType, uly=None, instId=None):
        params = {'instType': instType, 'uly': uly, 'instId': instId}
        return self._requests(OPEN_INTEREST, params)

    # Get Funding Rate
    def get_funding_rate(self, instId):
        params = {'instId': instId}
        return self._requests(FUNDING_RATE, params)
    
    # Get ETH2.0 Staking
    def get_eth2_staking(self, days = 30):
        params = {"days": days, "t": int(time.time() * 1000)}
        return self._requests(ETH2_STAKING, params)

    # Get Funding Rate History
    def funding_rate_history(self, instId, after=None, before=None, limit=None):
        params = {'instId': instId, 'after': after, 'before': before, 'limit': limit}
        return self._requests(FUNDING_RATE_HISTORY, params)
    
    # async Get Funding Rate History
    async def asyncGet_funding_history(self, instId: str, after=None, before=None, limit=None) -> dict:
        params = {'instId': instId, 'after': after, 'before': before, 'limit': limit}
        return await self._async_requests(FUNDING_RATE_HISTORY, params)

    # Get Limit Price
    def get_price_limit(self, instId):
        params = {'instId': instId}
        return self._requests(PRICE_LIMIT, params)

    # Get Option Market Data
    def get_opt_summary(self, uly, expTime=None):
        params = {'uly': uly, 'expTime': expTime}
        return self._requests(OPT_SUMMARY, params)

    # Get Estimated Delivery/Excercise Price
    def get_estimated_price(self, instId):
        params = {'instId': instId}
        return self._requests(ESTIMATED_PRICE, params)

    # Get Discount Rate And Interest-Free Quota
    def discount_interest_free_quota(self, ccy=None):
        params = {'ccy': ccy}
        return self._requests(DICCOUNT_INTETEST_INFO, params)

    # Get System Time
    def get_system_time(self):
        return self._requests(SYSTEM_TIME)

    # Get Liquidation Orders
    def get_liquidation_orders(self, instType, mgnMode=None, instId=None, ccy=None, uly=None, alias=None, state=None, before=None,
                            after=None, limit=None):
        params = {'instType': instType, 'mgnMode': mgnMode, 'instId': instId, 'ccy': ccy, 'uly': uly,
                'alias': alias, 'state': state, 'before': before, 'after': after, 'limit': limit}
        return self._requests(LIQUIDATION_ORDERS, params)

    # Get Mark Price
    def get_mark_price(self, instType, uly=None, instId=None):
        params = {'instType': instType, 'uly': uly, 'instId': instId}
        return self._requests(MARK_PRICE, params)
    
    # Get Tickers
    def get_tickers(self, instType, uly=None, instFamily=None):
        params = {'instType': instType, 'uly': uly, 'instFamily': instFamily}
        return self._requests(TICKERS_INFO, params)

    # Get Tier
    def get_tier(self, instType, tdMode, instFamily=None, instId=None, tier=None, ccy = None):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        return self._requests(POSITION_TIER, params)
    
    # Get History Interest
    def get_interest_history(self, ccy: str=None, after: str|int = None, before: str|int = None, limit: int|str = None):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        return self._requests(LENDING_RATE_HISTORY, params)
    
    # Get Interest
    def get_interest(self, ccy: str=None):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        return self._requests(LENDING_RATE_SUMMARY, params)
    
    # Get Klines
    def get_candles(self, instId: str, bar: str = "1D", after: int|str = None, before: int|str = None, limit: int|str = 100):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        return self._requests(MARKET_CANDLES, params)
    
    # Get History Klines
    def get_candles(self, instId: str, bar: str = "1D", after: int|str = None, before: int|str = None, limit: int|str = 100):
        params = {k:v  for k, v in locals().items() if k != 'self' and v is not None}
        return self._requests(HISTORY_CANDLES, params)
