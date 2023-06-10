import json
import os

from ovos_backend_manager.apis import ADMIN
from pywebio.input import select, actions, input_group, input, TEXT, NUMBER, textarea
from pywebio.output import put_table, popup, put_code, put_image, use_scope


def microservices_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/microservices_config.png', 'rb').read()
        put_image(img)

    backend_config = ADMIN.get_backend_config()

    with use_scope("main_view", clear=True):
        put_table([
            ['Primary STT', backend_config["stt_servers"][0]]
        ])

    buttons = [{'label': 'Configure STT Server', 'value': "stt"},
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
        url = textarea("Enter STT servers (1 per line)",
                       placeholder="https://openvoiceos.org/stt\nhttps://fasterwhisper.ziggyai.online/stt",
                       required=True)
        backend_config["stt_servers"] = [u.strip() for u in url.split("\n") if u]
        popup(f"STT set to: {url}")
    elif opt == "secrets":
        data = input_group('Secret Keys', [
            input("WolframAlpha key", value=backend_config["microservices"]["wolfram_key"],
                  type=TEXT, name='wolfram'),
            input("OpenWeatherMap key", value=backend_config["microservices"]["owm_key"],
                  type=TEXT, name='owm')
        ])
        backend_config["microservices"]["wolfram_key"] = data["wolfram"]
        backend_config["microservices"]["owm_key"] = data["owm"]
        popup("Secrets updated!")
    elif opt == "smtp":
        # TODO  - ovos / neon endpoint

        if "smtp" not in backend_config["microservices"]["email"]:
            backend_config["microservices"]["email"]["smtp"] = {}

        data = input_group('SMTP Configuration', [
            input("Username", value=backend_config["microservices"]["email"]["smtp"].get("username", 'user'),
                  type=TEXT, name='username'),
            input("Password", value=backend_config["microservices"]["email"]["smtp"].get("password", '***********'),
                  type=TEXT, name='password'),
            input("Host", value=backend_config["microservices"]["email"]["smtp"].get("host", 'smtp.mailprovider.com'),
                  type=TEXT, name='host'),
            input("Port", value=backend_config["microservices"]["email"]["smtp"].get("port", '465'),
                  type=NUMBER, name='port')
        ])

        backend_config["microservices"]["email"]["smtp"]["username"] = data["username"]
        backend_config["microservices"]["email"]["smtp"]["password"] = data["password"]
        backend_config["microservices"]["email"]["smtp"]["host"] = data["host"]
        backend_config["microservices"]["email"]["smtp"]["port"] = data["port"]
        with popup(f"SMTP configuration for: {data['host']}"):
            put_code(json.dumps(data, ensure_ascii=True, indent=2), "json")

    ADMIN.update_backend_config(backend_config)

    microservices_menu(back_handler=back_handler)
