# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel
from pydantic import Field

from .base_models import APIResponse


class ManifestValidatePost(BaseModel):
    """Validate Manifest post model."""

    manifest_json: dict = Field(
        {},
        example={
            'manifest_name': 'Manifest1',
            'project_code': 'sampleproject',
            'attributes': {'attr1': 'a1', 'attr2': 'test cli upload'},
            'file_path': '/data/core-storage/sampleproject/raw/testf1',
        },
    )


class ManifestValidateResponse(APIResponse):
    """Validate Manifest Response class."""

    result: dict = Field({}, example={'code': 200, 'error_msg': '', 'result': 'Valid'})


class EnvValidatePost(BaseModel):
    """Validate Environment post model."""

    action: str
    environ: str
    zone: str


class EnvValidateResponse(APIResponse):
    """Validate Manifest Response class."""

    result: dict = Field({}, example={'code': 200, 'error_msg': '', 'result': 'valid'})
