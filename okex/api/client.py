import requests, hmac, base64, datetime, hashlib, yaml, os, yaml, aiohttp
import okex.api.consts as c
from requests.adapters import HTTPAdapter, Retry


class Client(object):
    
    def __init__(self) -> None:
        self.c = c
        self.api_key: str
        self.secret_key: str
        self.passphrase: str
        self.server_time: str
        self.api_url = self.c.API_URL
        self.header = {"accept": self.c.APPLICATION_JSON, "content-type": self.c.APPLICATION_JSON}
        self.name: str = ""
    
    def load_account_api(self) -> None:
        self.api_key, self.secret_key, self.passphrase = "", "", ""
        with open(f"{os.path.expanduser('~')}/.cr_assis/account_okex_api.yml", "rb") as f:
            data: list[dict] = yaml.load(f, Loader= yaml.SafeLoader)
        for info in data:
            if "name" in info.keys() and info["name"] == self.name:
                self.api_key = info["api_key"]
                self.secret_key = info["secret_key"]
                self.passphrase = info["passphrase"]
                
    def get_account_header(self, query: str, method: str = "GET"):
        self.header = {"accept": self.c.APPLICATION_JSON, "content-type": self.c.APPLICATION_JSON}
        timestamp = datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat(timespec='milliseconds').replace("+00:00", "Z")
        message = timestamp + method + query
        signature = base64.b64encode(hmac.new(bytes(self.secret_key, "utf-8"), bytes(message, "utf-8"), digestmod=hashlib.sha256).digest())
        self.header[self.c.OK_ACCESS_KEY] = self.api_key
        self.header[self.c.OK_ACCESS_SIGN] = signature
        self.header[self.c.OK_ACCESS_TIMESTAMP] = str(timestamp)
        self.header[self.c.OK_ACCESS_PASSPHRASE] = self.passphrase
    
    def parse_params_to_str(self, params: dict[str, str]):
        url = '?'
        for key, value in params.items():
            if value:
                url = url + str(key) + '=' + str(value) + '&'
        return url[0:-1]
    
    def _send_requests(self, query: str, method: str = "GET") -> requests.Response:
        session, retry = requests.Session(), Retry(connect=5, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter =  HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.get(url = self.api_url + query, headers=self.header) if method == self.c.GET else session.post(url = query, headers= self.header)
        return response
    
    async def _send_async_requests(self, query: str, method: str = "GET") -> dict:
        async with aiohttp.ClientSession() as session:
            if method == self.c.GET:
                async with session.get(self.api_url + query, headers=self.header) as response:
                    ret = await response.json() if response.status == 200 else {}
                await session.close()
            else:
                async with session.post(self.api_url + query, headers=self.header) as response:
                    ret = await response.json() if response.status == 200 else {}
                await session.close()
        return ret
    
    def _requests_public(self, query: str, method: str = "GET") -> requests.Response:
        self.header = {"accept": self.c.APPLICATION_JSON, "content-type": self.c.APPLICATION_JSON}
        return self._send_requests(query, method)
    
    def _requests_account(self, query: str, method: str = "GET") -> requests.Response:
        self.load_account_api() if not hasattr(self, "api_key") or self.api_key == "" else None
        self.get_account_header(query = query, method= method)
        return self._send_requests(query, method)
    
    def _requests(self, query: str, params: dict = {}, method: str = "GET") -> requests.Response:
        url = query + self.parse_params_to_str(params)
        response = self._requests_public(url, method) if self.name == "" else self._requests_account(url, method)
        return response
    
    async def _async_requests(self, query: str, params: dict = {}, method: str = "GET") -> dict:
        url = query + self.parse_params_to_str(params)
        response = await self._async_requests_public(url, method) if self.name == "" else await self._async_requests_account(url, method)
        return response
    
    async def _async_requests_public(self, query: str, method: str = "GET") -> dict:
        self.header = {"accept": self.c.APPLICATION_JSON, "content-type": self.c.APPLICATION_JSON}
        return await self._send_async_requests(query, method)
    
    async def _async_requests_account(self, query: str, method: str = "GET") -> dict:
        self.load_account_api() if not self.api_key or self.api_key == "" else None
        self.get_account_header(query = query, method= method)
        return await self._send_async_requests(query, method)