import os

from ovos_local_backend.configuration import CONFIGURATION
from pywebio.input import actions
from pywebio.output import put_table, popup, use_scope, put_image


def selene_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/selene_proxy.png', 'rb').read()
        put_image(img)

    if CONFIGURATION["selene"]["enabled"]:
        buttons = [{'label': "View configuration", 'value': "view"},
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
        buttons = [{'label': "View configuration", 'value': "view"},
                   {'label': "Enable Selene", 'value': "selene"}]

    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?", buttons=buttons)
    if opt == "main":
        back_handler()
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
    if opt == "view":
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
    else:
        CONFIGURATION.store()

    selene_menu(back_handler=back_handler)
