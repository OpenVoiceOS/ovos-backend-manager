import json
import os
import time
from uuid import uuid4

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.metrics import JsonMetricDatabase
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.database.utterances import JsonUtteranceDatabase
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase
from ovos_local_backend.utils import generate_code
from ovos_local_backend.utils.geolocate import get_location_config
from pywebio import start_server
from pywebio.input import textarea, select, actions, checkbox, input_group, input, TEXT, NUMBER
from pywebio.output import put_text, put_table, put_markdown, popup, put_code

STT_CONFIGS = {
    "OpenVoiceOS (google proxy)": {"module": "ovos-stt-plugin-server", "url": "https://stt.openvoiceos.com/stt"},
    "Selene": {"module": "ovos-stt-plugin-selene", "url": "https://api.mycroft.ai"},
    "Vosk (en-us) - small": {"module": "ovos-stt-plugin-vosk",
                             "model": "http://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"},
    "Vosk (en-us) - large": {"module": "ovos-stt-plugin-vosk",
                             "model": "https://alphacephei.com/vosk/models/vosk-model-en-us-aspire-0.2.zip"},
    "Vosk (fr) - small": {"module": "ovos-stt-plugin-vosk",
                          "model": "https://alphacephei.com/vosk/models/vosk-model-small-fr-pguyot-0.3.zip"},
    "Vosk (fr) - large": {"module": "ovos-stt-plugin-vosk",
                          "model": "https://github.com/pguyot/zamia-speech/releases/download/20190930/kaldi-generic-fr-tdnn_f-r20191016.tar.xz"},
    "Vosk (de) - small": {"module": "ovos-stt-plugin-vosk",
                          "model": "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip"},
    "Vosk (de) - large": {"module": "ovos-stt-plugin-vosk",
                          "model": "https://alphacephei.com/vosk/models/vosk-model-de-0.6.zip"},
    "Vosk (es)": {"module": "ovos-stt-plugin-vosk",
                  "model": "https://alphacephei.com/vosk/models/vosk-model-small-es-0.3.zip"},
    "Vosk (pt)": {"module": "ovos-stt-plugin-vosk",
                  "model": "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"},
    "Vosk (it)": {"module": "ovos-stt-plugin-vosk",
                  "model": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.4.zip"},
    "Vosk (ca)": {"module": "ovos-stt-plugin-vosk",
                  "model": "https://alphacephei.com/vosk/models/vosk-model-small-ca-0.4.zip"},
    "Vosk (nl) - small": {"module": "ovos-stt-plugin-vosk",
                          "model": "https://alphacephei.com/vosk/models/vosk-model-nl-spraakherkenning-0.6-lgraph.zip"},
    "Vosk (nl) - large": {"module": "ovos-stt-plugin-vosk",
                          "model": "https://alphacephei.com/vosk/models/vosk-model-nl-spraakherkenning-0.6.zip"}
}


def _device_uuid_menu(uuid, view=False, identity=None):
    device = DeviceDatabase().get_device(uuid)
    if device:
        if view:
            with popup(f'UUID: {device.uuid}'):

                if identity:
                    put_markdown(f'### identity2.json')
                    put_code(json.dumps(identity, indent=4), "json")

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

        opt = actions(label="What would you like to do?",
                      buttons=[{'label': '<- Go Back', 'value': "main"},
                               {'label': "View device configuration", 'value': "view"},
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
                               {'label': 'Delete device', 'value': "delete"}])
        with DeviceDatabase() as db:
            if opt == "main":
                _device_menu()
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
                        _device_menu()
                        return
                    _device_uuid_menu(uuid)
                    return
            if opt == "identity":
                identity = {"uuid": device.uuid,
                            "expires_at": time.time() + 99999999999999,
                            "accessToken": device.token,
                            "refreshToken": device.token}
                _device_uuid_menu(uuid, view=True, identity=identity)
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

            db.update_device(device)

        popup("Device updated!")

        _device_uuid_menu(uuid, view=opt == "view")
    else:
        popup(f"Device not found! Please verify uuid")
        _device_menu()


def _selene_menu(view=False):
    if view:
        with popup("Selene Proxy Configuration"):
            put_table([
                ['Enabled', CONFIGURATION["selene"]["enabled"]],
                ['Host', CONFIGURATION["selene"]["url"]],
                ['Version', CONFIGURATION["selene"]["version"]],
                ['Identity', CONFIGURATION["selene"]["identity_file"]],
                ['Proxy Pairing Enabled', CONFIGURATION["selene"]["proxy_pairing"]],
                ['Proxy Weather', CONFIGURATION["selene"]["proxy_weather"]],
                ['Proxy WolframAlpha', CONFIGURATION["selene"]["proxy_wolfram"]],
                ['Proxy Geolocation', CONFIGURATION["selene"]["proxy_geolocation"]],
                ['Proxy Email', CONFIGURATION["selene"]["proxy_email"]],
                ['Download Location', CONFIGURATION["selene"]["download_location"]],
                ['Download Preferences', CONFIGURATION["selene"]["download_prefs"]],
                ['Download Skill Settings', CONFIGURATION["selene"]["download_settings"]],
                ['Upload Skill Settings', CONFIGURATION["selene"]["upload_settings"]],
                ['Force 2 way Skill Settings sync', CONFIGURATION["selene"]["force2way"]],
                ['OpenDataset opt in', CONFIGURATION["selene"]["opt_in"]],
                ['Upload Metrics', CONFIGURATION["selene"]["upload_metrics"]],
                ['Upload Wake Words', CONFIGURATION["selene"]["upload_wakewords"]],
                ['Upload Utterances', CONFIGURATION["selene"]["upload_utterances"]]
            ])

    if CONFIGURATION["selene"]["enabled"]:
        buttons = [{'label': '<- Go Back', 'value': "main"},
                   {'label': "View configuration", 'value': "view"},
                   {'label': "Disable Selene", 'value': "selene"}]

        label = "Enable Proxy Pairing" if CONFIGURATION["selene"]["proxy_pairing"] else "Disable Proxy Pairing"
        buttons.insert(-2, {'label': label, 'value': "proxy"})
        label = "Enable Weather Proxy" if CONFIGURATION["selene"]["proxy_weather"] else "Disable Weather Proxy"
        buttons.insert(-2, {'label': label, 'value': "weather"})
        label = "Enable WolframAlpha Proxy" if CONFIGURATION["selene"][
            "proxy_wolfram"] else "Disable WolframAlpha Proxy"
        buttons.insert(-2, {'label': label, 'value': "wolfram"})
        label = "Enable Geolocation Proxy" if CONFIGURATION["selene"][
            "proxy_geolocation"] else "Disable Geolocation Proxy"
        buttons.insert(-2, {'label': label, 'value': "geolocation"})
        label = "Enable Email Proxy" if CONFIGURATION["selene"]["proxy_email"] else "Disable Email Proxy"
        buttons.insert(-2, {'label': label, 'value': "email"})
        label = "Enable Location Download" if CONFIGURATION["selene"][
            "download_location"] else "Disable Location Download"
        buttons.insert(-2, {'label': label, 'value': "location"})
        label = "Enable Preferences Download" if CONFIGURATION["selene"][
            "download_prefs"] else "Disable Preferences Download"
        buttons.insert(-2, {'label': label, 'value': "prefs"})
        label = "Enable SkillSettings Download" if CONFIGURATION["selene"][
            "download_settings"] else "Disable SkillSettings Download"
        buttons.insert(-2, {'label': label, 'value': "download_settings"})
        label = "Enable SkillSettings Upload" if CONFIGURATION["selene"][
            "upload_settings"] else "Disable SkillSettings Upload"
        buttons.insert(-2, {'label': label, 'value': "upload_settings"})
        label = "Enable forced 2way sync" if CONFIGURATION["selene"]["force2way"] else "Disable forced 2way sync"
        buttons.insert(-2, {'label': label, 'value': "2way"})
        label = "Enable Open Dataset Opt In" if CONFIGURATION["selene"]["opt_in"] else "Disable Open Dataset Opt In"
        buttons.insert(-2, {'label': label, 'value': "opt_in"})
        label = "Enable Metrics Upload" if CONFIGURATION["selene"]["upload_metrics"] else "Disable Metrics Upload"
        buttons.insert(-2, {'label': label, 'value': "metrics"})
        label = "Enable Wake Words Upload" if CONFIGURATION["selene"][
            "upload_wakewords"] else "Disable Wake Words Upload"
        buttons.insert(-2, {'label': label, 'value': "ww"})
        label = "Enable Utterances Upload" if CONFIGURATION["selene"][
            "upload_utterances"] else "Disable Utterances Upload"
        buttons.insert(-2, {'label': label, 'value': "stt"})

    else:
        buttons = [{'label': '<- Go Back', 'value': "main"},
                   {'label': "View configuration", 'value': "view"},
                   {'label': "Enable Selene", 'value': "selene"}
                   ]

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        _main_menu()
        return
    elif opt == "geolocation":
        CONFIGURATION["selene"]["proxy_geolocation"] = not CONFIGURATION["selene"]["proxy_geolocation"]
    elif opt == "weather":
        CONFIGURATION["selene"]["proxy_weather"] = not CONFIGURATION["selene"]["proxy_weather"]
    elif opt == "wolfram":
        CONFIGURATION["selene"]["proxy_wolfram"] = not CONFIGURATION["selene"]["proxy_wolfram"]
    elif opt == "email":
        CONFIGURATION["selene"]["proxy_email"] = not CONFIGURATION["selene"]["proxy_email"]
    elif opt == "proxy":
        CONFIGURATION["selene"]["proxy_pairing"] = not CONFIGURATION["selene"]["proxy_pairing"]
    elif opt == "location":
        CONFIGURATION["selene"]["download_location"] = not CONFIGURATION["selene"]["download_location"]
    elif opt == "prefs":
        CONFIGURATION["selene"]["download_prefs"] = not CONFIGURATION["selene"]["download_prefs"]
    elif opt == "download_settings":
        CONFIGURATION["selene"]["download_settings"] = not CONFIGURATION["selene"]["download_settings"]
    elif opt == "upload_settings":
        CONFIGURATION["selene"]["upload_settings"] = not CONFIGURATION["selene"]["upload_settings"]
    elif opt == "2way":
        CONFIGURATION["selene"]["force2way"] = not CONFIGURATION["selene"]["force2way"]
    elif opt == "opt_in":
        CONFIGURATION["selene"]["opt_in"] = not CONFIGURATION["selene"]["opt_in"]
    elif opt == "selene":
        CONFIGURATION["selene"]["enabled"] = not CONFIGURATION["selene"]["enabled"]
    elif opt == "stt":
        CONFIGURATION["selene"]["upload_utterances"] = not CONFIGURATION["selene"]["upload_utterances"]
    elif opt == "ww":
        CONFIGURATION["selene"]["upload_wakewords"] = not CONFIGURATION["selene"]["upload_wakewords"]
    elif opt == "metrics":
        CONFIGURATION["selene"]["upload_metrics"] = not CONFIGURATION["selene"]["upload_metrics"]

    _selene_menu(view=opt == "view")


def _microservices_menu(view=False):
    selene = CONFIGURATION["selene"]["enabled"]
    if view:
        with popup("Microservices Configuration"):
            put_table([
                ['STT module', CONFIGURATION["stt"]["module"]],
                ['OVOS microservices fallback enabled', CONFIGURATION["microservices"]["ovos_fallback"]],

                ['WolframAlpha provider', CONFIGURATION["microservices"]["wolfram_provider"]],
                ['Weather provider', CONFIGURATION["microservices"]["weather_provider"]],

                ['Selene WolframAlpha proxy enabled', selene and CONFIGURATION["selene"]["proxy_wolfram"]],
                ['Selene OpenWeatherMap proxy enabled', selene and CONFIGURATION["selene"]["proxy_weather"]],
                ['Selene Geolocation proxy enabled', selene and CONFIGURATION["selene"]["proxy_geolocation"]],
                ['Selene Email proxy enabled', selene and CONFIGURATION["selene"]["proxy_email"]],

                ['WolframAlpha Key', CONFIGURATION["microservices"]["wolfram_key"]],
                ['OpenWeatherMap Key', CONFIGURATION["microservices"]["owm_key"]]
            ])

    buttons = [{'label': '<- Go Back', 'value': "main"},
               {'label': "View configuration", 'value': "view"},
               {'label': 'Configure STT', 'value': "stt"},
               {'label': 'Configure Secrets', 'value': "secrets"},
               {'label': 'Configure SMTP', 'value': "smtp"},
               {'label': 'Configure Wolfram Alpha', 'value': "wolfram"},
               {'label': 'Configure Weather', 'value': "weather"}
               ]

    if CONFIGURATION["microservices"]["ovos_fallback"]:
        buttons.insert(-2, {'label': 'Disable OVOS microservices fallback', 'value': "ovos"})
    else:
        buttons.insert(-2, {'label': 'Enable OVOS microservices fallback', 'value': "ovos"})

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        _main_menu()
        return
    elif opt == "weather":
        opts = ["ovos", "selene"] if selene else ["ovos"]
        if CONFIGURATION["microservices"]["owm_key"]:
            opts.append("local")
        provider = select("Choose a weather provider", opts)
        CONFIGURATION["microservices"]["owm_provider"] = provider
        if provider == "selene":
            CONFIGURATION["selene"]["proxy_weather"] = True
    elif opt == "wolfram":
        opts = ["ovos", "selene"] if selene else ["ovos"]
        if CONFIGURATION["microservices"]["wolfram_key"]:
            opts.append("local")
        provider = select("Choose a WolframAlpha provider", opts)
        CONFIGURATION["microservices"]["wolfram_provider"] = provider
        if provider == "selene":
            CONFIGURATION["selene"]["proxy_wolfram"] = True
    elif opt == "ovos":
        CONFIGURATION["microservices"]["ovos_fallback"] = not CONFIGURATION["microservices"]["ovos_fallback"]
        if CONFIGURATION["microservices"]["ovos_fallback"]:
            with popup("OVOS microservices fallback enabled"):
                put_text(
                    "wolfram alpha and weather requests will be proxied trough OVOS services if local keys get rate limited/become invalid/are not set")
        else:
            with popup("OVOS microservices fallback disabled"):
                put_text("please set your own wolfram alpha and weather keys")
    elif opt == "stt":
        opts = list(STT_CONFIGS.keys())
        if "Selene" in opts and not selene:
            opts.remove("Selene")
        stt = select("Choose a speech to text engine", opts)
        cfg = dict(STT_CONFIGS[stt])
        m = cfg.pop("module")
        CONFIGURATION["stt"]["module"] = m
        CONFIGURATION["stt"][m] = cfg
        with popup(f"STT set to: {stt}"):
            put_code(json.dumps(cfg, ensure_ascii=True, indent=2), "json")
    elif opt == "secrets":
        data = input_group('Secret Keys', [
            input("WolframAlpha key", value=CONFIGURATION["microservices"]["wolfram_key"],
                  type=TEXT, name='wolfram'),
            input("OpenWeatherMap key", value=CONFIGURATION["microservices"]["owm_key"],
                  type=TEXT, name='owm')
        ])
        CONFIGURATION["microservices"]["wolfram_key"] = data["wolfram"]
        CONFIGURATION["microservices"]["owm_key"] = data["owm"]
        popup("Secrets updated!")
    elif opt == "smtp":
        if "smtp" not in CONFIGURATION["email"]:
            CONFIGURATION["email"]["smtp"] = {}

        data = input_group('SMTP Configuration', [
            input("Username", value=CONFIGURATION["email"]["smtp"].get("username", 'user'),
                  type=TEXT, name='username'),
            input("Password", value=CONFIGURATION["email"]["smtp"].get("password", '***********'),
                  type=TEXT, name='password'),
            input("Host", value=CONFIGURATION["email"]["smtp"].get("host", 'smtp.mailprovider.com'),
                  type=TEXT, name='host'),
            input("Port", value=CONFIGURATION["email"]["smtp"].get("port", '465'),
                  type=NUMBER, name='port')
        ])

        CONFIGURATION["email"]["smtp"]["username"] = data["username"]
        CONFIGURATION["email"]["smtp"]["password"] = data["password"]
        CONFIGURATION["email"]["smtp"]["host"] = data["host"]
        CONFIGURATION["email"]["smtp"]["port"] = data["port"]
        with popup(f"SMTP configuration for: {data['host']}"):
            put_code(json.dumps(data, ensure_ascii=True, indent=2), "json")

    CONFIGURATION.store()
    _microservices_menu(view=opt == "view")


def _backend_menu(view=False):
    if view:
        with popup("Backend Configuration"):
            put_table([
                ['Backend Port', CONFIGURATION["backend_port"]],
                ['Device Authentication enabled', not CONFIGURATION["skip_auth"]],
                ['Location override enabled', CONFIGURATION["override_location"]],
                ['IP Geolocation enabled', CONFIGURATION["geolocate"]],
                ['Selene Proxy enabled', CONFIGURATION["selene"]["enabled"]],
                ['Default TTS', CONFIGURATION["default_tts"]],
                ['Default Wake Word', CONFIGURATION["default_ww"]],
                ['Default date format', CONFIGURATION["date_format"]],
                ['Default time format', CONFIGURATION["time_format"]],
                ['Default system units', CONFIGURATION["system_unit"]]
            ])
            put_markdown(f'### Default location:')
            put_table([
                ['City', CONFIGURATION["default_location"]["city"]["name"]],
                ['State', CONFIGURATION["default_location"]["city"]["state"]["name"]],
                ['Country', CONFIGURATION["default_location"]["city"]["state"]["country"]["name"]],
                ['Country Code', CONFIGURATION["default_location"]["city"]["state"]["country"]["code"]],
                ['Latitude', CONFIGURATION["default_location"]["coordinate"]["latitude"]],
                ['Longitude', CONFIGURATION["default_location"]["coordinate"]["longitude"]],
                ['Timezone Code', CONFIGURATION["default_location"]["timezone"]["code"]]
            ])

    auth = 'Enable device auth' if not CONFIGURATION["skip_auth"] else 'Disable device auth'

    buttons = [{'label': '<- Go Back', 'value': "main"},
               {'label': "View configuration", 'value': "view"},
               {'label': auth, 'value': "auth"},
               {'label': 'Set default location', 'value': "geo"},
               {'label': 'Set default voice', 'value': "tts"},
               {'label': 'Set default wake word', 'value': "ww"},
               {'label': 'Set default email', 'value': "email"},
               {'label': 'Set default date format', 'value': "date"},
               {'label': 'Set default time format', 'value': "time"},
               {'label': 'Set default system units', 'value': "unit"}
               ]
    if CONFIGURATION["override_location"]:
        buttons.insert(-2, {'label': 'Enable IP geolocation', 'value': "ip_geo"})
    else:
        buttons.insert(-2, {'label': 'Enable location override', 'value': "loc_override"})

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        _main_menu()
        return
    elif opt == "tts":
        tts = select("Choose a voice", list(CONFIGURATION["tts_configs"].keys()))
        CONFIGURATION["default_tts"] = tts
        with popup(f"Default TTS set to: {tts}"):
            put_code(json.dumps(CONFIGURATION["tts_configs"][tts], ensure_ascii=True, indent=2), "json")
    elif opt == "ww":
        ww = select("Choose a wake word",
                    list(CONFIGURATION["ww_configs"].keys()))
        CONFIGURATION["default_ww"] = ww
        with popup(f"Default wake word set to: {ww}"):
            put_code(json.dumps(CONFIGURATION["ww_configs"][ww], ensure_ascii=True, indent=2), "json")
    elif opt == "geo":
        loc = textarea("Enter an address",
                       placeholder="Anywhere street Any city Nº234",
                       required=True)
        data = get_location_config(loc)
        CONFIGURATION["default_location"] = data
        with popup(f"Default location set to: {loc}"):
            put_code(json.dumps(data, ensure_ascii=True, indent=2), "json")
    elif opt == "loc_override":
        CONFIGURATION["override_location"] = True
        CONFIGURATION["geolocate"] = False
        popup("Location override enabled!")
    elif opt == "ip_geo":
        CONFIGURATION["geolocate"] = True
        CONFIGURATION["override_location"] = False
        popup("IP Geolocation enabled!")
    elif opt == "auth":
        CONFIGURATION["skip_auth"] = not CONFIGURATION["skip_auth"]
        if CONFIGURATION["skip_auth"]:
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
    if opt == "view":
        _backend_menu(view=True)
    else:
        CONFIGURATION.store()
        _backend_menu(view=False)


def _metrics_menu():
    buttons = []
    db = JsonMetricDatabase()
    if not len(db):
        popup("No metrics uploaded yet!")
        _database_menu()
        return

    for m in db:
        name = f"{m['metric_id']}-{m['metric_type']}"
        buttons.append({'label': name, 'value': m['metric_id']})
    buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a metric to inspect",
                  buttons=buttons)
    if opt == "main":
        _database_menu()
        return
    # id == db_position + 1
    name = f"{opt}-{db[opt - 1]['metric_type']}"
    with popup(name):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    _metrics_menu()


def _ww_menu():
    buttons = []
    db = JsonWakeWordDatabase()
    if not len(db):
        popup("No wake words uploaded yet!")
        _database_menu()
        return

    for m in db:
        name = f"{m['wakeword_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['wakeword_id']})
    buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a WakeWord recording",
                  buttons=buttons)
    if opt == "main":
        _database_menu()
        return
    # id == db_position + 1
    name = f"{opt}-{db[opt - 1]['transcription']}"
    with popup(name):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    _ww_menu()


def _utt_menu():
    buttons = []
    db = JsonUtteranceDatabase()
    if not len(db):
        popup("No utterances uploaded yet!")
        _database_menu()
        return

    for m in db:
        name = f"{m['utterance_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['utterance_id']})
    buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a Utterance recording",
                  buttons=buttons)
    if opt == "main":
        _database_menu()
        return

    # id == db_position + 1
    name = f"{opt}-{db[opt - 1]['transcription']}"
    with popup(name):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    _utt_menu()


def _database_menu():
    opt = actions(label="What would you like to do?",
                  buttons=[{'label': '<- Go Back', 'value': "main"},
                           {'label': 'View Metrics', 'value': "metrics"},
                           {'label': 'View Wake Words', 'value': "ww"},
                           {'label': 'View Utterances', 'value': "utt"},
                           {'label': 'Delete metrics database', 'value': "delete_metrics"},
                           {'label': 'Delete wake words database', 'value': "delete_ww"},
                           {'label': 'Delete utterances database', 'value': "delete_utts"}
                           ])

    if opt == "metrics":
        _metrics_menu()
    if opt == "ww":
        _ww_menu()
    if opt == "utt":
        _utt_menu()
    if opt == "delete_metrics":
        with popup("Are you sure you want to delete the metrics database?"):
            put_text("this can not be undone, proceed with caution!")
            put_text("ALL metrics will be lost")
        opt = actions(label="Delete metrics database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            os.remove(JsonMetricDatabase().db.path)
            _main_menu()
        else:
            _database_menu()
        return
    if opt == "delete_ww":
        with popup("Are you sure you want to delete the wake word database?"):
            put_text("this can not be undone, proceed with caution!")
            put_text("ALL wake word recordings will be lost")
        opt = actions(label="Delete wake words database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            # TODO - also remove files from path
            os.remove(JsonWakeWordDatabase().db.path)
            _main_menu()
        else:
            _database_menu()
        return
    if opt == "delete_utts":
        with popup("Are you sure you want to delete the utterance database?"):
            put_text("this can not be undone, proceed with caution!")
            put_text("ALL utterance recordings will be lost")
        opt = actions(label="Delete utterance recordings database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            # TODO - also remove files from path
            os.remove(JsonUtteranceDatabase().db.path)
            _main_menu()
        else:
            _database_menu()
        return
    if opt == "main":
        _main_menu()
        return
    _database_menu()


def _device_menu():
    devices = {uuid: f"{device['name']}@{device['device_location']}"
               for uuid, device in DeviceDatabase().items()}
    buttons = [{'label': '<- Go Back', 'value': "main"}] + \
              [{'label': d, 'value': uuid} for uuid, d in devices.items()] + \
              [{'label': 'Delete device database', 'value': "delete_devices"}]
    if devices:
        uuid = actions(label="What device would you like to manage?",
                       buttons=buttons)
        if uuid == "main":
            _main_menu()
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
                _main_menu()
            else:
                _device_menu()
            return
        else:
            _device_uuid_menu(uuid, view=True)
    else:
        popup("No devices paired yet!")
        _main_menu()


def _pair_device():
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

    _device_uuid_menu(uuid, view=True, identity=identity)


def _main_menu():
    popup("hello there!")
    opt = actions(label="What would you like to do?",
                  buttons=[{'label': 'Pair a device', 'value': "pair"},
                           {'label': 'Manage Devices', 'value': "device"},
                           {'label': 'Manage Datasets', 'value': "db"},
                           {'label': 'Configure Backend', 'value': "backend"},
                           {'label': 'Configure Microservices', 'value': "services"},
                           {'label': 'Configure Selene Proxy', 'value': "selene"}])
    if opt == "pair":
        _pair_device()
    elif opt == "services":
        _microservices_menu()
    elif opt == "db":
        _database_menu()
    elif opt == "backend":
        _backend_menu(view=False)
    elif opt == "selene":
        _selene_menu()
    elif opt == "device":
        _device_menu()


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
    _main_menu()


if __name__ == '__main__':
    start_server(app, port=36535, debug=True)