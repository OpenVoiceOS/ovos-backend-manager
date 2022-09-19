import json
import time
from uuid import uuid4

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.utils import generate_code
from ovos_local_backend.utils.geolocate import get_location_config
from pywebio import start_server
from pywebio.input import textarea, select, actions
from pywebio.output import put_text, put_table, put_markdown, popup, put_code


def _device_menu(uuid, info=True):
    device = DeviceDatabase().get_device(uuid)
    if device:
        if info:
            put_markdown(f'# Device UUID: {device.uuid}')
            put_table([
                ['Name', device.name],
                ['Location', device.device_location],
                ['Email', device.email],
                ['Date Format', device.date_format],
                ['Time Format', device.time_format],
                ['System Unit', device.system_unit],
                ['Opt In', device.opt_in],
                ['Lang', device.lang],
                ['Default Wake Word', device.default_ww],
                ['Default Voice', device.default_tts]
            ])
            put_markdown(f'### Geolocation:')
            put_table([
                ['City', device.location["city"]["name"]],
                ['State', device.location["city"]["state"]["name"]],
                ['Country', device.location["city"]["state"]["country"]["name"]],
                ['Country Code', device.location["city"]["state"]["country"]["code"]],
                ['Latitude', device.location["coordinate"]["latitude"]],
                ['Longitude', device.location["coordinate"]["longitude"]],
                ['Timezone Code', device.location["timezone"]["code"]]
            ])

        opt = actions(label="What would you like to do?",
                      buttons=[{'label': 'Change device name', 'value': "name"},
                               {'label': 'Change indoor location', 'value': "location"},
                               {'label': 'Change geographical location', 'value': "geo"},
                               {'label': 'Change wake word', 'value': "ww"},
                               {'label': 'Change voice', 'value': "tts"},
                               {'label': 'Change email', 'value': "email"},
                               {'label': 'Change date format', 'value': "date"},
                               {'label': 'Change time format', 'value': "time"},
                               {'label': 'Change system units', 'value': "unit"},
                               {'label': 'Admin Menu', 'value': "admin"}])
        with DeviceDatabase() as db:
            if opt == "admin":
                _admin_menu()
                return
            if opt == "tts":
                tts = select("Choose a voice",
                             list(CONFIGURATION["tts_configs"].keys()))
                device.default_tts = CONFIGURATION["tts_configs"][tts]["module"]
                device.default_tts_cfg = CONFIGURATION["tts_configs"][tts]
            if opt == "ww":
                ww = select("Choose a wake word",
                            list(CONFIGURATION["ww_configs"].keys()))
                device.default_ww = ww
                device.default_ww_cfg = CONFIGURATION["ww_configs"][ww]
            if opt == "date":
                date = select("Change date format",
                              ['DMY', 'MDY'])
                device.date_format = date
            if opt == "time":
                time = select("Change time format",
                              ['full', 'short'])
                device.time_format = time
            if opt == "unit":
                unit = select("Change time format",
                              ['metric', 'imperial'])
                device.system_unit = unit
            if opt == "email":
                email = textarea("Enter your device email",
                                 placeholder="notify@me.com",
                                 required=True)
                device.email = email
            if opt == "name":
                name = textarea("Enter your device name",
                                placeholder="OVOS Mark2",
                                required=True)
                device.name = name
            if opt == "location":
                loc = textarea("Enter your device indoor location",
                               placeholder="kitchen",
                               required=True)
                device.device_location = loc
            if opt == "geo":
                loc = textarea("Enter an address",
                               placeholder="Anywhere street Any city Nº234",
                               required=True)
                data = get_location_config(loc)
                device.location = data

            db.update_device(device)

        popup("Device updated!")

        _device_menu(uuid)
    else:
        popup(f"Device not found! Please verify uuid")
        _admin_menu()


def _admin_menu():
    opt = actions(label="What would you like to do?",
                  buttons=[{'label': 'Get device info', 'value': "info"},
                           {'label': 'Pair a device', 'value': "pair"}])
    if opt == "pair":
        uuid = str(uuid4())
        code = generate_code()
        token = f"{code}:{uuid}"
        # add device to db
        with DeviceDatabase() as db:
            db.add_device(uuid, token)

        identity = {"uuid": uuid,
                    "expires_at": time.time() + 99999999999999,
                    "accessToken": token,
                    "refreshToken": token}

        with popup("Device Paired!"):
            put_markdown(f'### identity2.json')
            put_code(json.dumps(identity, indent=4), "json")

        _device_menu(uuid, info=True)
    elif opt == "info":
        uuid = textarea("Select a device",
                        placeholder="check the uuid in the identity file (identity2.json)",
                        required=True)
        _device_menu(uuid, info=True)


def _admin_auth():
    admin_key = textarea("insert your admin_key, this should have been set in your backend configuration file",
                         placeholder="SuperSecretPassword1!",
                         required=True)
    if CONFIGURATION["admin_key"] != admin_key:
        popup("INVALID ADMIN KEY!")
        _admin_auth()


def app():
    if not CONFIGURATION["admin_key"]:
        put_text("This personal backend instance does not have the admin interface exposed")
        return
    _admin_auth()
    _admin_menu()


if __name__ == '__main__':
    start_server(app, port=36535, debug=True)
