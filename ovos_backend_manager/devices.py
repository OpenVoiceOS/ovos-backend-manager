import json
import os
import time
from uuid import uuid4

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.utils import generate_code
from ovos_local_backend.utils.geolocate import get_location_config
from pywebio.input import textarea, select, actions, checkbox
from pywebio.output import put_text, put_table, put_markdown, popup, put_code


def device_menu(uuid, back_handler=None):
    buttons = [{'label': "View device configuration", 'value': "view"},
               {'label': "View device identity", 'value': "identity"},
               {'label': 'Change device name', 'value': "name"},
               {'label': 'Change placement', 'value': "location"},
               {'label': 'Change geographical location', 'value': "geo"},
               {'label': 'Change wake word', 'value': "ww"},
               {'label': 'Change voice', 'value': "tts"},
               {'label': 'Change email', 'value': "email"},
               {'label': 'Change opt-in', 'value': "opt-in"},
               {'label': 'Change date format', 'value': "date"},
               {'label': 'Change time format', 'value': "time"},
               {'label': 'Change system units', 'value': "unit"},
               {'label': 'Delete device', 'value': "delete"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    device = DeviceDatabase().get_device(uuid)
    if device:
        opt = actions(label="What would you like to do?",
                      buttons=buttons)
        with DeviceDatabase() as db:
            if opt == "main":
                device_select(back_handler)
                return
            if opt == "delete":
                with popup("Are you sure you want to delete the device?"):
                    put_text("this can not be undone, proceed with caution!")
                    opt = actions(label="Delete device?",
                                  buttons=[{'label': "yes", 'value': True},
                                           {'label': "no", 'value': False}])
                    if opt:
                        db.delete_device(uuid)
                        db.store()
                        device_select(back_handler)
                        return
                    device_menu(uuid, back_handler=back_handler)
                    return
            if opt == "opt-in":
                opt_in = checkbox("Opt-in to open dataset",
                                  [{'label': 'opt-in', 'value': True},
                                   {'label': 'selene_blacklist', 'value': False}])
                device.opt_in = opt_in[0]
                if opt_in[1]:
                    CONFIGURATION["selene"]["opt_in_blacklist"].append(uuid)
                    CONFIGURATION.store()
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
                tim = select("Change time format",
                             ['full', 'short'])
                device.time_format = tim
            if opt == "unit":
                unit = select("Change system units",
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
                loc = textarea("Enter your device placement",
                               placeholder="kitchen",
                               required=True)
                device.device_location = loc
            if opt == "geo":
                loc = textarea("Enter an address",
                               placeholder="Anywhere street Any city Nº234",
                               required=True)
                data = get_location_config(loc)
                device.location = data

            if opt == "identity":
                identity = {"uuid": device.uuid,
                            "expires_at": time.time() + 99999999999999,
                            "accessToken": device.token,
                            "refreshToken": device.token}
                with popup(f'UUID: {device.uuid}'):
                    put_markdown(f'### identity2.json')
                    put_code(json.dumps(identity, indent=4), "json")
            elif opt == "view":
                with popup(f'UUID: {device.uuid}'):
                    put_markdown(f'### Device Data:')
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
            else:
                db.update_device(device)
                popup("Device updated!")

        device_menu(uuid, back_handler=back_handler)
    else:
        popup(f"Device not found! Please verify uuid")
        device_select(back_handler)


def device_select(back_handler=None):
    devices = {uuid: f"{device['name']}@{device['device_location']}"
               for uuid, device in DeviceDatabase().items()}
    buttons = [{'label': d, 'value': uuid} for uuid, d in devices.items()] + \
              [{'label': 'Delete device database', 'value': "delete_devices"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if devices:
        uuid = actions(label="What device would you like to manage?",
                       buttons=buttons)
        if uuid == "main":
            back_handler()
            return
        elif uuid == "delete_devices":
            with popup("Are you sure you want to delete the device database?"):
                put_text("this can not be undone, proceed with caution!")
                put_text("ALL devices will be unpaired")
            opt = actions(label="Delete devices database?",
                          buttons=[{'label': "yes", 'value': True},
                                   {'label': "no", 'value': False}])
            if opt:
                os.remove(DeviceDatabase().path)
                back_handler()
            else:
                device_select(back_handler)
            return
        else:
            device_menu(uuid, back_handler=back_handler)
    else:
        popup("No devices paired yet!")
        if back_handler:
            back_handler()


def instant_pair(back_handler=None):
    uuid = str(uuid4())
    code = generate_code()
    token = f"{code}:{uuid}"
    # add device to db
    with DeviceDatabase() as db:
        db.add_device(uuid, token)

    with popup("Device paired!"):
        put_table([
            ['UUID', uuid],
            ['CODE', code],
            ['TOKEN', token]
        ])

    device_menu(uuid, back_handler=back_handler)
