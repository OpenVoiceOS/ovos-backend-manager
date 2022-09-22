from pywebio import start_server

from ovos_backend_manager.app import app


def main(port=36535):
    start_server(app, port=port, debug=False)


if __name__ == '__main__':
    start_server(app, port=36535, debug=True)
