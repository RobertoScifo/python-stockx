import aiohttp
import asyncio

from ...exceptions import (
    StockXNotInitialized,
    stockx_request_error,
)
from ...models import Response


GRANT_TYPE = 'refresh_token'
REFRESH_URL = 'https://accounts.stockx.com/oauth/token'
REFRESH_TIME = 3600
AUDIENCE = 'gateway.stockx.com'


class StockXAPIClient:
    
    def __init__(
            self,
            hostname: str,
            version: str,
            x_api_key: str,
            client_id: str,
            client_secret: str,
            refresh_token: str, # TODO: later implement token as well or authentication
    ) -> None:
        self.url = f'https://{hostname}/{version}'
        self.x_api_key = x_api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        
        self._initialized: bool = False
        self._session: aiohttp.ClientSession = None
        self._refresh_task: asyncio.Task = None

    async def initialize(self) -> None:
        refresh = self._refresh_session()
        self._refresh_task = asyncio.create_task(refresh)
        await asyncio.sleep(2)

    async def close(self) -> None:
        if self._session:
            await self._session.close()
        if self._refresh_task:
            self._refresh_task.cancel()
        
    async def get(self, endpoint: str, params: dict = None) -> Response:
        return await self._do('GET', endpoint, params=params)
    
    async def put(self, endpoint: str, data: dict = None) -> Response:
        return await self._do('PUT', endpoint, data=data)
    
    async def post(self, endpoint: str, data: dict = None) -> Response:
        return await self._do('POST', endpoint, data=data)

    async def patch(self, endpoint: str, data: dict = None) -> Response:
        return await self._do('PATCH', endpoint, data=data)
    
    async def delete(self, endpoint: str) -> Response:
        return await self._do('DELETE', endpoint)
    
    async def _do(
            self, 
            method: str,
            endpoint: str, 
            params: dict = None,
            data: dict = None
    ) -> Response:
        if not self._initialized:
            raise StockXNotInitialized()
        
        if params:
            params = {k: v for k, v in params.items() if v is not None}
        if data:
            data = {k: v for k, v in data.items() if v is not None}

        url = f'{self.url}{endpoint}'
        try:
            async with self._session.request(
                method,
                url,
                params=params,
                json=data
            ) as response:
                data = await response.json()
                if 299 >= response.status >= 200:
                    return Response(
                        status_code=response.status, 
                        message=response.reason, 
                        data=data
                    )
                raise stockx_request_error(
                    message=data.get('errorMessage', None), 
                    status_code=response.status
                )
        except aiohttp.ClientError as e:
            raise stockx_request_error('Request failed.') from e 
                
    async def _refresh_session(self) -> None:
        while True:
            if self._session: 
                await self._session.close() # TODO: don't close session, just change token
            headers = await self._login()
            self._session = aiohttp.ClientSession(headers=headers) 
            self._initialized = True
            await asyncio.sleep(REFRESH_TIME)

    async def _login(self) -> dict:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        refresh_data = {
            'grant_type': GRANT_TYPE,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'audience': AUDIENCE,
            'refresh_token': self.refresh_token
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                REFRESH_URL, headers=headers, data=refresh_data
            ) as response:
                payload = await response.json()
                token = payload['access_token']
                return {
                    'Authorization': f'Bearer {token}',
                    'x-api-key': self.x_api_key
                }
            

            