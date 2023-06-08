import json
import os

from pywebio.input import textarea, select, actions
from pywebio.output import put_table, put_markdown, popup, put_code, put_image, use_scope
from ovos_backend_manager.apis import ADMIN, GEO

# TODO - from backend
CONFIGURATION = {}


def backend_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/backend_config.png', 'rb').read()
        put_image(img)

    with use_scope("main_view", clear=True):
        put_table([
            ['Backend Port', CONFIGURATION["server"]["port"]],
            ['Device Authentication enabled', not CONFIGURATION["server"]["skip_auth"]],
            ['Location override enabled', CONFIGURATION["server"]["override_location"]],
            ['IP Geolocation enabled', CONFIGURATION["server"]["geolocate"]],
            ['Default TTS', CONFIGURATION["tts"]["module"]],
            ['Default Wake Word', CONFIGURATION["listener"]["wake_word"]],
            ['Default date format', CONFIGURATION["date_format"]],
            ['Default time format', CONFIGURATION["time_format"]],
            ['Default system units', CONFIGURATION["system_unit"]]
        ])
        put_markdown(f'### Default location:')
        put_table([
            ['Timezone Code', CONFIGURATION["location"]["timezone"]["code"]],
            ['City', CONFIGURATION["location"]["city"]["name"]],
            ['State', CONFIGURATION["location"]["city"]["state"]["name"]],
            ['Country', CONFIGURATION["location"]["city"]["state"]["country"]["name"]],
            ['Country Code', CONFIGURATION["location"]["city"]["state"]["country"]["code"]],
            ['Latitude', CONFIGURATION["location"]["coordinate"]["latitude"]],
            ['Longitude', CONFIGURATION["location"]["coordinate"]["longitude"]]
        ])

    auth = 'Enable device auth' if not CONFIGURATION["server"]["skip_auth"] else 'Disable device auth'

    buttons = [{'label': auth, 'value': "auth"},
               {'label': 'Set default location', 'value': "geo"},
               {'label': 'Set default voice', 'value': "tts"},
               {'label': 'Set default wake word', 'value': "ww"},
               {'label': 'Set default email', 'value': "email"},
               {'label': 'Set default date format', 'value': "date"},
               {'label': 'Set default time format', 'value': "time"},
               {'label': 'Set default system units', 'value': "unit"}
               ]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if CONFIGURATION["server"]["override_location"]:
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
        # TODO - opm scan
        tts = select("Choose a voice", list(k for k in CONFIGURATION["tts"].keys()
                                            if k not in ["module"]))
        CONFIGURATION["tts"]["module"] = tts
        with popup(f"Default TTS set to: {tts}"):
            put_code(json.dumps(CONFIGURATION["tts"][tts], ensure_ascii=True, indent=2), "json")
    elif opt == "ww":
        # TODO - opm scan
        ww = select("Choose a wake word",
                    list(CONFIGURATION["hotwords"].keys()))
        CONFIGURATION["listener"]["wake_word"] = ww
        with popup(f"Default wake word set to: {ww}"):
            put_code(json.dumps(CONFIGURATION["ww_configs"][ww], ensure_ascii=True, indent=2), "json")
    elif opt == "geo":
        loc = textarea("Enter an address",
                       placeholder="Anywhere street Any city Nº234",
                       required=True)
        data = GEO.get_geolocation(loc)
        CONFIGURATION["location"] = data
        with popup(f"Default location set to: {loc}"):
            put_code(json.dumps(data, ensure_ascii=True, indent=2), "json")
    elif opt == "loc_override":
        CONFIGURATION["server"]["override_location"] = True
        CONFIGURATION["server"]["geolocate"] = False
        popup("Location override enabled!")
    elif opt == "ip_geo":
        CONFIGURATION["server"]["geolocate"] = True
        CONFIGURATION["server"]["override_location"] = False
        popup("IP Geolocation enabled!")
    elif opt == "auth":
        CONFIGURATION["server"]["skip_auth"] = not CONFIGURATION["server"]["skip_auth"]
        if CONFIGURATION["server"]["skip_auth"]:
            popup("Device authentication enabled!")
        else:
            popup("Device authentication disabled! Pairing will not be needed")
    elif opt == "date":
        CONFIGURATION["date_format"] = select("Change date format",
                                              ['DMY', 'MDY'])
        popup(f"Default date format set to: {CONFIGURATION['date_format']}")
    elif opt == "time":
        CONFIGURATION["time_format"] = select("Change time format",
                                              ['full', 'short'])
        popup(f"Default time format set to: {CONFIGURATION['time_format']}")
    elif opt == "unit":
        CONFIGURATION["system_unit"] = select("Change system units",
                                              ['metric', 'imperial'])
        popup(f"Default system units set to: {CONFIGURATION['system_unit']}")
    elif opt == "email":
        email = textarea("Enter default notifications email",
                         placeholder="notify@me.com",
                         required=True)
        CONFIGURATION["email"]["recipient"] = email

    if opt != "view":
        ADMIN.update_backend_config(CONFIGURATION)

    backend_menu(back_handler=back_handler)
