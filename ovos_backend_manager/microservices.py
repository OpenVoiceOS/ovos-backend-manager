import json
import os

from ovos_local_backend.configuration import CONFIGURATION
from pywebio.input import select, actions, input_group, input, TEXT, NUMBER
from pywebio.output import put_text, put_table, popup, put_code, put_image, use_scope

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


def microservices_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/microservices_config.png', 'rb').read()
        put_image(img)

    selene = CONFIGURATION["selene"]["enabled"]
    buttons = [{'label': "View configuration", 'value': "view"},
               {'label': 'Configure STT', 'value': "stt"},
               {'label': 'Configure Secrets', 'value': "secrets"},
               {'label': 'Configure SMTP', 'value': "smtp"},
               {'label': 'Configure Wolfram Alpha', 'value': "wolfram"},
               {'label': 'Configure Weather', 'value': "weather"},
               {'label': 'Configure Geolocation', 'value': "geo"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if CONFIGURATION["microservices"]["ovos_fallback"]:
        buttons.insert(-2, {'label': 'Disable OVOS microservices fallback', 'value': "ovos"})
    else:
        buttons.insert(-2, {'label': 'Enable OVOS microservices fallback', 'value': "ovos"})

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        with use_scope("main_view", clear=True):
            if back_handler:
                back_handler()
        return
    elif opt == "geo":
        opts = ["local"]  # TODO - ovos endpoint
        if selene and CONFIGURATION["selene"]["proxy_geolocation"]:
            opts.append("selene")
        provider = select("Choose a weather provider", opts)
        # TODO - implement selection backend side, config key below not live
        CONFIGURATION["microservices"]["geolocation_provider"] = provider
    elif opt == "weather":
        opts = ["ovos"]
        if CONFIGURATION["microservices"]["owm_key"]:
            opts.append("local")
        if selene and CONFIGURATION["selene"]["proxy_weather"]:
            opts.append("selene")
        provider = select("Choose a weather provider", opts)
        CONFIGURATION["microservices"]["owm_provider"] = provider
    elif opt == "wolfram":
        opts = ["ovos"]
        if CONFIGURATION["microservices"]["wolfram_key"]:
            opts.append("local")
        if selene and CONFIGURATION["selene"]["proxy_wolfram"]:
            opts.append("selene")
        provider = select("Choose a WolframAlpha provider", opts)
        CONFIGURATION["microservices"]["wolfram_provider"] = provider
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
        # TODO - checkbox for selene proxy
        # TODO - ovos endpoint

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

    if opt == "view":
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
    else:
        CONFIGURATION.store()

    microservices_menu(back_handler=back_handler)
