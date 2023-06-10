# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from ovos_backend_client.api import DatabaseApi, AdminApi, GeolocationApi, DatasetApi, BackendType
from ovos_config import Configuration

_cfg = Configuration()["server"]

print(_cfg)

DB = DatabaseApi(_cfg["admin_key"],
                 url=_cfg["url"], backend_type=BackendType.PERSONAL)
ADMIN = AdminApi(_cfg["admin_key"],
                 url=_cfg["url"], backend_type=BackendType.PERSONAL)
GEO = GeolocationApi(backend_type=BackendType.OFFLINE)  # helper
DATASET = DatasetApi(url=_cfg["url"], backend_type=BackendType.PERSONAL)  # upload
