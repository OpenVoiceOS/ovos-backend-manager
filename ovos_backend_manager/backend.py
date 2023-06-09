import json
import os

from pywebio.input import textarea, select, actions
from pywebio.output import put_table, put_markdown, popup, put_code, put_image, use_scope
from ovos_backend_manager.apis import ADMIN, GEO, DB


def backend_menu(back_handler=None):
    backend_config = ADMIN.get_backend_config()

    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/backend_config.png', 'rb').read()
        put_image(img)

    with use_scope("main_view", clear=True):
        put_table([
            ['Backend Port', backend_config["server"]["port"]],
            ['Device Authentication enabled', not backend_config["server"].get("skip_auth", False)],
            ['Location override enabled', backend_config["server"].get("override_location", False)],
            ['IP Geolocation enabled', backend_config["server"].get("geolocate", True)],
            ['Default Voice Id', backend_config["default_values"]["voice_id"]],
            ['Default Wake Word Id', backend_config["default_values"]["ww_id"]],
            ['Default date format', backend_config["date_format"]],
            ['Default time format', backend_config["time_format"]],
            ['Default system units', backend_config["system_unit"]]
        ])
        put_markdown(f'### Default location:')
        put_table([
            ['Timezone Code', backend_config["location"]["timezone"]["code"]],
            ['City', backend_config["location"]["city"]["name"]],
            ['State', backend_config["location"]["city"]["state"]["name"]],
            ['Country', backend_config["location"]["city"]["state"]["country"]["name"]],
            ['Country Code', backend_config["location"]["city"]["state"]["country"]["code"]],
            ['Latitude', backend_config["location"]["coordinate"]["latitude"]],
            ['Longitude', backend_config["location"]["coordinate"]["longitude"]]
        ])

    auth = 'Enable device auth' if not backend_config["server"].get("skip_auth", False) else 'Disable device auth'

    wws = {v["ww_id"]: v for v in DB.list_ww_definitions()}
    voices = {v["voice_id"]: v for v in DB.list_voice_definitions()}

    buttons = [{'label': auth, 'value': "auth"},
               {'label': 'Set default location', 'value': "geo"},
               {'label': 'Set default email', 'value': "email"},
               {'label': 'Set default date format', 'value': "date"},
               {'label': 'Set default time format', 'value': "time"},
               {'label': 'Set default system units', 'value': "unit"}
               ]
    if len(wws):
        buttons.append({'label': 'Set default wake word', 'value': "ww"})
    if len(voices):
        buttons.append({'label': 'Set default voice', 'value': "tts"})
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if backend_config["server"]["override_location"]:
        buttons.insert(-2, {'label': 'Enable IP geolocation', 'value': "ip_geo"})
    else:
        buttons.insert(-2, {'label': 'Enable location override', 'value': "loc_override"})

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        with use_scope("main_view", clear=True):
            if back_handler:
                back_handler()
        return
    elif opt == "tts":

        tts = select("Choose a voice", list(voices.keys()))
        backend_config["default_values"]["voice_id"] = tts
        with popup(f"Default TTS set to: {tts}"):
            put_code(json.dumps(voices[tts]["tts_config"],
                                ensure_ascii=False, indent=2), "json")
    elif opt == "ww":
        ww = select("Choose a wake word",
                    list(wws.keys()))
        backend_config["default_values"]["ww_id"] = ww
        with popup(f"Default wake word set to: {ww}"):
            put_code(json.dumps(wws[ww]["ww_config"],
                                ensure_ascii=False, indent=2), "json")
    elif opt == "geo":
        loc = textarea("Enter an address",
                       placeholder="Anywhere street Any city Nº234",
                       required=True)
        data = GEO.get_geolocation(loc)
        backend_config["location"] = data
        with popup(f"Default location set to: {loc}"):
            put_code(json.dumps(data, ensure_ascii=False, indent=2), "json")
    elif opt == "loc_override":
        backend_config["server"]["override_location"] = True
        backend_config["server"]["geolocate"] = False
        popup("Location override enabled!")
    elif opt == "ip_geo":
        backend_config["server"]["geolocate"] = True
        backend_config["server"]["override_location"] = False
        popup("IP Geolocation enabled!")
    elif opt == "auth":
        backend_config["server"]["skip_auth"] = not backend_config["server"].get("skip_auth", False)
        if backend_config["server"]["skip_auth"]:
            popup("Device authentication enabled!")
        else:
            popup("Device authentication disabled! Pairing will not be needed")
    elif opt == "date":
        backend_config["date_format"] = select("Change date format",
                                              ['DMY', 'MDY'])
        popup(f"Default date format set to: {backend_config['date_format']}")
    elif opt == "time":
        backend_config["time_format"] = select("Change time format",
                                              ['full', 'short'])
        popup(f"Default time format set to: {backend_config['time_format']}")
    elif opt == "unit":
        backend_config["system_unit"] = select("Change system units",
                                              ['metric', 'imperial'])
        popup(f"Default system units set to: {backend_config['system_unit']}")
    elif opt == "email":
        email = textarea("Enter default notifications email",
                         placeholder="notify@me.com",
                         required=True)
        backend_config["microservices"]["email"]["recipient"] = email

    if opt != "view":
        ADMIN.update_backend_config(backend_config)

    backend_menu(back_handler=back_handler)
