# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LoggerFactory
from fastapi import APIRouter
from fastapi import Depends
from fastapi_utils.cbv import cbv

from app.resources.helpers import get_dataset
from app.resources.helpers import get_dataset_versions
from app.resources.helpers import list_datasets

from ...config import ConfigClass
from ...models.base_models import EAPIResponseCode
from ...models.dataset_models import DatasetDetailResponse
from ...models.dataset_models import DatasetListResponse
from ...resources.dependencies import jwt_required
from ...resources.error_handler import ECustomizedError
from ...resources.error_handler import catch_internal
from ...resources.error_handler import customized_error_template

router = APIRouter()
_API_TAG = 'V1 dataset'
_API_NAMESPACE = 'api_dataset'


@cbv(router)
class APIDataset:
    current_identity: dict = Depends(jwt_required)

    def __init__(self):
        self._logger = LoggerFactory(
            _API_NAMESPACE,
            level_default=ConfigClass.LOG_LEVEL_DEFAULT,
            level_file=ConfigClass.LOG_LEVEL_FILE,
            level_stdout=ConfigClass.LOG_LEVEL_STDOUT,
            level_stderr=ConfigClass.LOG_LEVEL_STDERR,
        ).get_logger()

    @router.get(
        '/datasets',
        tags=[_API_TAG],
        response_model=DatasetListResponse,
        summary='Get dataset list that user have access to',
    )
    @catch_internal(_API_NAMESPACE)
    async def list_datasets(self, page=0, page_size=10):
        """Get the dataset list that user have access to."""
        """
        Summary:
            The api will call the dataset service to get
            the dataset list that user have access to.
        Parameter:
            - page(int): page number
            - page_size(str): page size
        return:
            - result(dict): dataset list
        """
        self._logger.info('API list_datasets'.center(80, '-'))
        api_response = DatasetListResponse()
        username = self.current_identity['username']

        self._logger.info(f'User request with identity: {self.current_identity}')
        dataset_list = await list_datasets(username, page, page_size)
        self._logger.info(f'Getting user datasets: {dataset_list}')
        api_response.result = dataset_list
        api_response.code = EAPIResponseCode.success
        return api_response.json_response()

    @router.get(
        '/dataset/{dataset_code}',
        tags=[_API_TAG],
        response_model=DatasetDetailResponse,
        summary='Get dataset detail based on the dataset code',
    )
    @catch_internal(_API_NAMESPACE)
    async def get_dataset(self, dataset_code, page=0, page_size=10):
        """
        Summary:
            The api will integrate with dataset detail and versions
            api to have a joint response for cli tool.
        Path Parameter:
            - dataset_code(str): unique identifier of dataset
        Parameter:
            - page(int): page number
            - page_size(str): page size
        return:
            - result(dict): dataset detail info
        """

        self._logger.info('API get_dataset'.center(80, '-'))
        api_response = DatasetDetailResponse()
        username = self.current_identity['username']

        self._logger.info(f'User request with identity: {self.current_identity}')
        node = await get_dataset(dataset_code)
        self._logger.info(f'Getting user dataset node: {node}')
        if not node:
            api_response.code = EAPIResponseCode.not_found
            api_response.error_msg = customized_error_template(ECustomizedError.DATASET_NOT_FOUND)
            return api_response.json_response()
        elif node.get('creator') != username:
            api_response.code = EAPIResponseCode.forbidden
            api_response.error_msg = customized_error_template(ECustomizedError.PERMISSION_DENIED)
            return api_response.json_response()

        node_geid = node.get('id')
        dataset_query_event = {'dataset_geid': node_geid, 'page': page, 'page_size': page_size}
        self._logger.info(f'Dataset query: {dataset_query_event}')

        versions = await get_dataset_versions(dataset_query_event)
        self._logger.info(f'Dataset versions: {versions}')
        dataset_detail = {'general_info': node, 'version_detail': versions, 'version_no': len(versions)}
        api_response.result = dataset_detail
        api_response.code = EAPIResponseCode.success
        return api_response.json_response()
