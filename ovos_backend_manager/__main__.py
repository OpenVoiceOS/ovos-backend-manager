from ovos_config.utils import init_module_config

init_module_config("ovos_backend_manager",
                   "ovos_backend_manager",
                   {"config_filename": "ovos_backend_manager.conf"})

if __name__ == '__main__':
    from ovos_backend_manager.app import main

    main(port=36535, debug=False)
