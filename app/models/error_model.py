# Copyright (C) 2022-2023 Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE, Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

class ValidationError(Exception):
    def __init__(self, message='Validation Failed'):
        super().__init__(message)
        self.error_msg = message


class InvalidEncryptionError(Exception):
    def __init__(self, message='Invalid encryption'):
        super().__init__(message)
