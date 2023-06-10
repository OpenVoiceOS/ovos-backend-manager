from ovos_config import Configuration, USER_CONFIG
from pywebio.input import actions
from pywebio.output import put_text, use_scope, put_image

from ovos_backend_manager.backend import backend_menu
from ovos_backend_manager.datasets import datasets_menu
from ovos_backend_manager.devices import device_select, instant_pair
from ovos_backend_manager.metrics import metrics_menu
from ovos_backend_manager.microservices import microservices_menu
from ovos_backend_manager.oauth import oauth_menu
from ovos_backend_manager.apis import ADMIN


def main_menu():
    with use_scope("logo", clear=True):
        from os.path import dirname
        img = open(f'{dirname(__file__)}/res/personal_backend.png', 'rb').read()
        put_image(img)

    opt = actions(label="What would you like to do?",
                  buttons=[{'label': 'Pair a device', 'value': "pair"},
                           {'label': 'Manage Devices', 'value': "device"},
                           {'label': 'Manage Metrics', 'value': "metrics"},
                           {'label': 'Manage Datasets', 'value': "db"},
                           {'label': 'OAuth Applications', 'value': "oauth"},
                           {'label': 'Configure Backend', 'value': "backend"},
                           {'label': 'Configure Microservices', 'value': "services"}])
    if opt == "pair":
        instant_pair(back_handler=main_menu)
    elif opt == "services":
        microservices_menu(back_handler=main_menu)
    elif opt == "oauth":
        oauth_menu(back_handler=main_menu)
    elif opt == "db":
        datasets_menu(back_handler=main_menu)
    elif opt == "backend":
        backend_menu(back_handler=main_menu)
    elif opt == "device":
        device_select(back_handler=main_menu)
    elif opt == "metrics":
        metrics_menu(back_handler=main_menu)


def start():
    if not Configuration()["server"]["admin_key"]:
        put_text(f"You need to set admin key in {USER_CONFIG}")
        exit(1)

    try:
        ADMIN.get_backend_config()
    except Exception as e:
        print(e)
        put_text(f"Backend refused admin key or does not have AdminApi enabled")
        exit(2)

    with use_scope("logo", clear=True):
        from os.path import dirname
        img = open(f'{dirname(__file__)}/res/personal_backend.png', 'rb').read()
        put_image(img)

    main_menu()
