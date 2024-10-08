# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

import enum
from functools import wraps

from ..models.base_models import APIResponse
from ..models.base_models import EAPIResponseCode


def catch_internal(api_namespace):
    """decorator to catch internal server error."""

    def decorator(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exce:
                respon = APIResponse()
                respon.code = EAPIResponseCode.internal_error
                respon.result = None
                err = api_namespace + ' ' + str(exce)
                respon.error_msg = customized_error_template(ECustomizedError.INTERNAL) % err
                return respon.json_response()

        return inner

    return decorator


class ECustomizedError(enum.Enum):
    """Enum of customized errors."""

    INTERNAL = 'INTERNAL'
    FILE_NOT_FOUND = 'FILE_NOT_FOUND'
    MANIFEST_NOT_FOUND = 'MANIFEST_NOT_FOUND'
    INVALID_ATTRIBUTE = 'INVALID_ATTRIBUTE'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    MISSING_REQUIRED_ATTRIBUTES = 'MISSING_REQUIRED_ATTRIBUTES'
    INVALID_CHOICE = 'INVALID_CHOICE'
    FIELD_REQUIRED = 'FIELD_REQUIRED'
    TEXT_TOO_LONG = 'TEXT_TOO_LONG'
    PROJECT_NOT_FOUND = 'PROJECT_NOT_FOUND'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    USER_NOT_IN_PROJECT = 'USER_NOT_IN_PROJECT'
    MISSING_INFO = 'MISSING_INFO'
    FILE_FOLDER_ONLY = 'FILE_FOLDER_ONLY'
    DATASET_NOT_FOUND = 'DATASET_NOT_FOUND'
    INVALID_ZONE = 'INVALID_ZONE'
    INVALID_VARIABLE = 'INVALID_VARIABLE'


def customized_error_template(customized_error: ECustomizedError):
    """get error template."""
    return {
        'INTERNAL': '[Internal] %s',
        'FILE_NOT_FOUND': 'File Not Exist',
        'MANIFEST_NOT_FOUND': 'Manifest Not Exist %s',
        'INVALID_ATTRIBUTE': 'Invalid Attribute %s',
        'TOKEN_EXPIRED': 'Token Expired',
        'MISSING_REQUIRED_ATTRIBUTES': 'Missing Required Attribute %s',
        'INVALID_CHOICE': 'Invalid Choice Field %s',
        'FIELD_REQUIRED': 'Field Required %s',
        'TEXT_TOO_LONG': 'Text Too Long %s',
        'PROJECT_NOT_FOUND': 'Project not found',
        'PERMISSION_DENIED': 'Permission Denied',
        'USER_NOT_IN_PROJECT': 'User not in the project',
        'MISSING_INFO': '%s is required',
        'FILE_FOLDER_ONLY': 'Can only work on file or folder not in Trash Bin',
        'DATASET_NOT_FOUND': 'Cannot found given dataset code',
        'INVALID_ZONE': 'Invalid zone',
        'INVALID_VARIABLE': 'Invalid variable',
    }.get(customized_error.name, 'Unknown Error')


class APIException(Exception):
    def __init__(self, status_code: int, error_msg: str):
        self.status_code = status_code
        self.content = {
            'code': self.status_code,
            'error_msg': error_msg,
            'result': '',
        }
