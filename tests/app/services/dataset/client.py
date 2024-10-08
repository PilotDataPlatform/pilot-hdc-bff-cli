# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from typing import Mapping

from fastapi import Depends
from httpx import AsyncClient
from httpx import Response

from app.config import Settings
from app.config import get_settings


class DatasetServiceClient:
    """Client for dataset service."""

    def __init__(self, endpoint: str, timeout: int) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = AsyncClient(timeout=timeout)

    async def list_datasets(self, parameters: Mapping[str, str]) -> Response:
        """Get list of datasets."""

        return await self.client.get(f'{self.endpoint_v1}/datasets/', params=parameters)


def get_dataset_service_client(settings: Settings = Depends(get_settings)) -> DatasetServiceClient:
    """Get Dataset Service Client as a FastAPI dependency."""

    return DatasetServiceClient(settings.DATASET_SERVICE, settings.SERVICE_CLIENT_TIMEOUT)
