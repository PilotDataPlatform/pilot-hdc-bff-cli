# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from collections.abc import Mapping

from httpx import Response

from app.components.request.context import RequestContextDependency
from app.components.request.http_client import HTTPClient
from app.config import SettingsDependency


class DatasetServiceClient:
    """Client for dataset service."""

    def __init__(self, endpoint: str, client: HTTPClient) -> None:
        self.endpoint_v1 = f'{endpoint}/v1'
        self.client = client

    async def list_datasets(self, parameters: Mapping[str, str]) -> Response:
        """Get list of datasets."""

        return await self.client.get(f'{self.endpoint_v1}/datasets/', params=parameters)


def get_dataset_service_client(
    request_context: RequestContextDependency, settings: SettingsDependency
) -> DatasetServiceClient:
    """Get Dataset Service Client as a FastAPI dependency."""

    return DatasetServiceClient(settings.DATASET_SERVICE.replace('/v1/', ''), request_context.client)
