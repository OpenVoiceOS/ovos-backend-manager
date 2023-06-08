import json
import os

from ovos_backend_client.api import AdminApi, BackendType
from ovos_plugin_manager.stt import get_stt_configs, get_stt_supported_langs, get_stt_lang_configs
from pywebio.input import select, actions, input_group, input, TEXT, NUMBER
from pywebio.output import put_table, popup, put_code, put_image, use_scope

from ovos_backend_manager.configuration import CONFIGURATION

BLACKLISTED_PLUGS = ["ovos-stt-plugin-selene"]


def _get_stt_opts(lang=None):
    STT_CONFIGS = {}
    if lang is not None:
        for p, data in get_stt_lang_configs(lang, include_dialects=True).items():
            if p in BLACKLISTED_PLUGS:
                continue
            if not data:
                continue
            for cfg in data:
                cfg["module"] = p
                cfg["display_name"] = f"{cfg['display_name']} [{p}]"
                STT_CONFIGS[cfg["display_name"]] = cfg
    else:
        for p, data in get_stt_configs().items():
            if p in BLACKLISTED_PLUGS:
                continue
            if not data:
                continue
            for lang, confs in data.items():
                for cfg in confs:
                    cfg["module"] = p
                    cfg["display_name"] = f"{cfg['display_name']} [{p}]"
                    STT_CONFIGS[cfg["display_name"]] = cfg
    return STT_CONFIGS


def microservices_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/microservices_config.png', 'rb').read()
        put_image(img)

    with use_scope("main_view", clear=True):
        put_table([
            ['STT module', CONFIGURATION["stt"]["module"]]
        ])

    buttons = [{'label': 'Configure STT', 'value': "stt"},
               {'label': 'Configure Secrets', 'value': "secrets"},
               {'label': 'Configure SMTP', 'value': "smtp"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        with use_scope("main_view", clear=True):
            if back_handler:
                back_handler()
        return
    elif opt == "stt":
        lang = select("Choose STT default language",
                      list(get_stt_supported_langs().keys()))
        cfgs = _get_stt_opts(lang)
        opts = list(cfgs.keys())
        stt = select("Choose a speech to text engine", opts)
        cfg = dict(cfgs[stt])
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
        # TODO  - ovos / neon endpoint

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

    admin = AdminApi(CONFIGURATION["server"].get("admin_key"),
                     url=CONFIGURATION["server"].get("url"),
                     backend_type=BackendType.PERSONAL)
    admin.update_backend_config(CONFIGURATION)

    microservices_menu(back_handler=back_handler)
