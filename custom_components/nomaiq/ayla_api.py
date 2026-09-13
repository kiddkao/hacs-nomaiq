import ayla_iot_unofficial

class AylaApi:
    def __init__(self, username, password, client_id, client_secret, session=None):
        self._api = ayla_iot_unofficial.new_ayla_api(
            username, password, client_id, client_secret, websession=session
        )

    async def async_login(self):
        await self._api.async_sign_in()

    def check_auth(self):
        self._api.check_auth()

    async def async_refresh_auth(self):
        await self._api.async_refresh_auth()

    async def async_get_devices(self):
        return await self._api.async_get_devices()
