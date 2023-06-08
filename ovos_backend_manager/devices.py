import json
import os
import time
from uuid import uuid4

from ovos_backend_manager.configuration import CONFIGURATION, DB
import random
from ovos_backend_client.api import GeolocationApi
from pywebio.input import textarea, select, actions, checkbox
from pywebio.output import put_text, put_table, put_markdown, popup, put_code, use_scope, put_image


def device_menu(uuid, back_handler=None):
    buttons = [{'label': "View device configuration", 'value': "view"},
               {'label': "View device location", 'value': "view_loc"},
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

    def update_info(d, l=False):
        with use_scope("main_view", clear=True):
            if l:
                put_markdown(f'### Geolocation:')
                put_table([
                    ['City', d.location["city"]["name"]],
                    ['State', d.location["city"]["state"]["name"]],
                    ['Country', d.location["city"]["state"]["country"]["name"]],
                    ['Country Code', d.location["city"]["state"]["country"]["code"]],
                    ['Latitude', d.location["coordinate"]["latitude"]],
                    ['Longitude', d.location["coordinate"]["longitude"]],
                    ['Timezone Code', d.location["timezone"]["code"]]
                ])
            else:
                put_markdown(f'### Configuration:')
                put_table([
                    ['Name', d.name],
                    ['Location', d.device_location],
                    ['Email', d.email],
                    ['Date Format', d.date_format],
                    ['Time Format', d.time_format],
                    ['System Unit', d.system_unit],
                    ['Opt In', d.opt_in],
                    ['Lang', d.lang],
                    ['Default Wake Word', d.default_ww],
                    ['Default Voice', d.default_tts]
                ])

    device = DB.get_device(uuid)
    if device:
        y = False
        opt = actions(label="What would you like to do?",
                      buttons=buttons)

        if opt == "main":
            with use_scope("main_view", clear=True):
                pass
            device_select(back_handler=back_handler)
            return
        elif opt == "delete":
            with popup("Are you sure you want to delete the device?"):
                put_text("this can not be undone, proceed with caution!")
                y = actions(label="Delete device?",
                            buttons=[{'label': "yes", 'value': True},
                                     {'label': "no", 'value': False}])
                if y:
                    DB.delete_device(uuid)
        elif opt == "opt-in":
            opt_in = checkbox("Open Dataset - device metrics and speech recordings",
                              [{'label': 'Store metrics and recordings',
                                'selected': device.opt_in,
                                'value': "opt_in"}])

            device["opt_in"] = "opt_in" in opt_in

        elif opt == "tts":
            # TODO - opm scan json
            tts = select("Choose a voice",
                         list(k for k in CONFIGURATION["tts"].keys() if k not in ["module"]))
            device["default_tts"] = CONFIGURATION["tts"]["module"]
            device["default_tts_cfg"] = CONFIGURATION["tts"][tts]
        elif opt == "ww":
            # TODO - opm scan json
            ww = select("Choose a wake word",
                        list(CONFIGURATION["hotwords"].keys()))
            device["default_ww"] = ww
            device["default_ww_cfg"] = CONFIGURATION["hotwords"][ww]
        elif opt == "date":
            date = select("Change date format",
                          ['DMY', 'MDY'])
            device["date_format"] = date
        elif opt == "time":
            tim = select("Change time format",
                         ['full', 'short'])
            device["time_format"] = tim
        elif opt == "unit":
            unit = select("Change system units",
                          ['metric', 'imperial'])
            device["system_unit"] = unit
        elif opt == "email":
            email = textarea("Enter your device email",
                             placeholder="notify@me.com",
                             required=True)
            device["email"] = email
        elif opt == "name":
            name = textarea("Enter your device name",
                            placeholder="OVOS Mark2",
                            required=True)
            device["name"] = name
        elif opt == "location":
            loc = textarea("Enter your device placement",
                           placeholder="kitchen",
                           required=True)
            device["device_location"] = loc
        elif opt == "geo":
            loc = textarea("Enter an address",
                           placeholder="Anywhere street Any city Nº234",
                           required=True)
            data = GeolocationApi().get_geolocation(loc)
            device["location"] = data
        elif opt == "identity":
            identity = {"uuid": device["uuid"],
                        "expires_at": time.time() + 99999999999999,
                        "accessToken": device["token"],
                        "refreshToken": device["token"]}
            with use_scope("main_view", clear=True):
                put_markdown(f'### identity2.json')
                put_code(json.dumps(identity, indent=4), "json")
        elif opt == "view_loc" or opt == "geo":
            update_info(device, True)
        else:
            update_info(device, False)

        if opt not in ["identity", "delete", "view_loc"]:
            DB.update_device(**device)
            popup("Device updated!")
        elif opt == "delete" and y:
            uuid = None
        device_menu(uuid, back_handler=back_handler)

    else:
        with use_scope("main_view", clear=True):
            pass
        device_select(back_handler=back_handler)


def device_select(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/devices.png', 'rb').read()
        put_image(img)

    devices = {device["uuid"]: f"{device['name']}@{device['device_location']}"
               for device in DB.list_devices()}
    buttons = [{'label': d, 'value': uuid} for uuid, d in devices.items()] + \
              [{'label': 'Delete device database', 'value': "delete_devices"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if devices:
        uuid = actions(label="What device would you like to manage?",
                       buttons=buttons)
        if uuid == "main":
            with use_scope("main_view", clear=True):
                if back_handler:
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
                for dev in DB.list_devices():
                    DB.delete_device(dev["uuid"])

                with use_scope("main_view", clear=True):
                    if back_handler:
                        back_handler()
            else:
                device_select(back_handler)
            return
        else:
            device_menu(uuid, back_handler=back_handler)
    else:
        popup("No devices paired yet!")
        if back_handler:
            with use_scope("main_view", clear=True):
                if back_handler:
                    back_handler()


def instant_pair(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/devices.png', 'rb').read()
        put_image(img)

    uuid = str(uuid4())
    code = f"{random.randint(100, 999)}ABC"
    token = f"{code}:{uuid}"

    # add device to db
    DB.add_device(uuid, token)

    with use_scope("main_view", clear=True):
        put_markdown("# Device paired!")
        put_table([
            ['UUID', uuid],
            ['CODE', code],
            ['TOKEN', token]
        ])

    device_menu(uuid, back_handler=back_handler)
