import base64
import json
from typing import Dict, Optional, Any

import requests
from edenai_apis.features import ProviderInterface, ImageInterface
from edenai_apis.features.image import BackgroundRemovalDataClass
from edenai_apis.loaders.data_loader import ProviderDataEnum
from edenai_apis.loaders.loaders import load_provider
from edenai_apis.utils.exception import ProviderException
from edenai_apis.utils.types import ResponseType


class PicsartApi(ProviderInterface, ImageInterface):
    provider_name = 'picsart'

    def __init__(self, api_key: Optional[str] = None):
        self.api_settings = load_provider(
            ProviderDataEnum.KEY, self.provider_name, api_keys=api_key or {}
        )
        self.base_image_api_url = self.api_settings["image_api_base_url"]  # "https://api.picsart.io/tools/1.0"
        self.api_key = self.api_settings["api_key"]
        self.headers = {
            "X-Picsart-API-Key": self.api_settings["api_key"],
            "Accept": "application/json",
            # "content-type": "multipart/form-data",
        }


    def image__background_removal(
            self,
            file: Optional[str] = None,
            file_url: Optional[str] = None,
            provider_params: Optional[Dict[str, Any]] = None,
    ) -> ResponseType[BackgroundRemovalDataClass]:
        url = f"{self.base_image_api_url}/removebg"

        if provider_params is None:
            provider_params = {}

        if file and not file_url:
            with open(file, "rb") as image_file:
                files = {"image": image_file}
                response = requests.post(url, files=files, data=provider_params, headers=self.headers)
        elif file_url and not file:
            provider_params["image_url"] = file_url
            response = requests.post(url, data=provider_params, headers=self.headers)
        else:
            raise ProviderException("No file or file_url provided")

        if response.status_code != 200:
            try:
                error_message = response.json()["error"]
            except (KeyError, json.JSONDecodeError):
                error_message = "Internal Server Error"
            raise ProviderException(error_message, code=response.status_code)

        result = response.json()
        image_url = result["data"]["url"]
        image_response = requests.get(image_url)
        image_b64 = base64.b64encode(image_response.content).decode("utf-8")

        return ResponseType[BackgroundRemovalDataClass](
            original_response=response.text,
            standardized_response=BackgroundRemovalDataClass(
                image_b64=image_b64,
                image_resource_url=image_url,
            ),
        )
