import json
import random
import urllib

from typing import Dict, TYPE_CHECKING

from cdm.utilities.network.cdm_http_request import CdmHttpRequest

if TYPE_CHECKING:
    from cdm.utilities.network.cdm_http_response import CdmHttpResponse


class NetworkAdapter:
    """ Network adapter is an abstract class that contains logic for adapters dealing with data across network.
    Please see GithubAdapter, ADLSAdapter or RemoteAdapter for usage of this class.
    When extending this class a user has to define CdmHttpClient with the specified endpoint and callback function in the constructor
    and can then use the class helper methods to set up Cdm HTTP requests and read data.
    If a user doesn't specify timeout, maximutimeout or number of retries in the config under 'httpConfig' property default values
    will be used as specified in the class.
    """

    DEFAULT_TIMEOUT = 2000

    DEFAULT_NUMBER_OF_RETRIES = 2

    DEFAULT_MAXIMUM_TIMEOUT = 10000

    DEFAULT_SHORTEST_WAIT_TIME = 500

    def __init__(self) -> None:
        self.timeout = self.DEFAULT_TIMEOUT  # type: int
        self.maximum_timeout = self.DEFAULT_MAXIMUM_TIMEOUT  # type: int
        self.number_of_retries = self.DEFAULT_NUMBER_OF_RETRIES  # type: int
        self.wait_time_callback = self._default_get_wait_time

    def _set_up_cdm_request(self, path: str, headers: Dict, method: str) -> 'CdmHttpRequest':
        request = CdmHttpRequest(path)

        request.headers = headers
        request.method = method
        request.timeout = self.timeout
        request.maximum_timeout = self.maximum_timeout
        request.number_of_retries = self.number_of_retries

        return request

    async def _read(self, request: 'CdmHttpRequest') -> str:
        result = await self._http_client.send_async(request, self.wait_time_callback)

        if result is None:
            raise Exception('The result of a request is undefined.')

        if result.is_successful is False:
            raise urllib.error.HTTPError(url=request.requested_url, code=result.status_code, msg='Failed to read', hdrs=result.response_headers, fp=None)

        return result.content

    def _default_get_wait_time(self, response: 'CdmHttpResponse', has_failed: bool, retry_number: int) -> int:
        """
        Callback function for a CDM Http client, it does exponential backoff.
        :param response: The response received by system's Http client.
        :param has_failed: Denotes whether the request has failed (usually an exception or 500 error).
        :param retry_number: The current retry number (starts from 1) up to the number of retries specified by CDM request
        :return: The time in milliseconds.
        """
        if response and response.is_successful and not has_failed:
            return None

        return random.randint(0, 2**retry_number) * self.DEFAULT_SHORTEST_WAIT_TIME

    def update_network_config(self, config: str) -> None:
        configs_json = json.loads(config)

        if configs_json.get('timeout') is not None:
            self.timeout = float(configs_json['timeout'])

        if configs_json.get('maximumTimeout') is not None:
            self.maximum_timeout = float(configs_json['maximumTimeout'])

        if configs_json.get('numberOfRetries') is not None:
            self.number_of_retries = int(configs_json['numberOfRetries'])

    def fetch_network_config(self):
        return {
            'timeout': self.timeout,
            'maximumTimeout': self.maximum_timeout,
            'numberOfRetries': self.number_of_retries
        }