import os

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from ovos_config.utils import init_module_config

init_module_config("ovos_backend_manager",
                   "ovos_backend_manager",
                   {"config_filename": "ovos_backend_manager.conf"})

import requests
from flask import Flask, request
from oauthlib.oauth2 import WebApplicationClient
from pywebio.platform.flask import webio_view

from ovos_backend_manager.apis import DB
from ovos_backend_manager.menu import start


app = Flask(__name__)

# `task_func` is PyWebIO task function
app.add_url_rule('/', 'webio_view', webio_view(start),
                 methods=['GET', 'POST', 'OPTIONS'])  # need GET,POST and OPTIONS methods


@app.route("/auth/callback/<oauth_id>", methods=['GET'])
def oauth_callback(oauth_id):
    """ user completed oauth, save token to db """
    params = dict(request.args)
    code = params["code"]

    data = DB.get_oauth_app(oauth_id)
    client_id = data["client_id"]
    client_secret = data["client_secret"]
    token_endpoint = data["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    client = WebApplicationClient(client_id)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(client_id, client_secret),
    ).json()

    DB.add_oauth_token(oauth_id, token_response)

    return params


def main(port=36535, debug=False):
    app.run(host="0.0.0.0", port=port, debug=debug)
    # start_server(app, port=port, debug=debug)
