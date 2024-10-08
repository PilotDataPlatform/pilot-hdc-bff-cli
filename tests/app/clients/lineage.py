# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from common import LineageClient as Lineage

from app.config import ConfigClass


class LineageClient:
    def __init__(self):
        self.client = Lineage(ConfigClass.ATLAS_API, ConfigClass.ATLAS_ADMIN, ConfigClass.ATLAS_PASSWD)

    async def create_lineage(
        self, input_id, output_id, input_path, output_path, container_code, action_type, description
    ):
        await self.client.create_lineage(
            input_id=input_id,
            output_id=output_id,
            input_name=input_path,
            output_name=output_path,
            project_code=container_code,
            pipeline_name=action_type,
            entity_type=ConfigClass.ATLAS_ENTITY_TYPE,
            description=description,
        )
