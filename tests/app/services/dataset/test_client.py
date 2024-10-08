# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.


class TestDatasetServiceClient:
    async def test_list_datasets_calls_dataset_service(self, httpx_mock, fake, dataset_service_client):
        parameters = fake.pydict(allowed_types=[str, int])

        query_string = '&'.join(f'{key}={value}' for key, value in parameters.items())

        httpx_mock.add_response(method='GET', url=f'{dataset_service_client.endpoint_v1}/datasets/?{query_string}')

        response = await dataset_service_client.list_datasets(parameters)

        assert response.status_code == 200
