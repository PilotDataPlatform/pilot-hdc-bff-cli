# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from pydantic import BaseModel
from pydantic import Field

from .base_models import APIResponse


class LineageCreatePost(BaseModel):
    project_code: str
    input_id: str
    output_id: str
    input_path: str
    output_path: str
    action_type: str
    description: str


class LineageCreateResponse(APIResponse):
    """Lineage Creation Response class."""

    result: dict = Field({}, example={'message': 'Succeed'})
