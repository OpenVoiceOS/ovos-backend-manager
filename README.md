# OpenVoiceOS Backend Manager

a simple UI for [ovos-personal-backend](https://github.com/OpenVoiceOS/ovos-personal-backend), utility to manage all
your devices

![](./screenshots/demo.gif)

## Install

`pip install ovos-backend-manager`

or from source

`pip install git+https://github.com/OpenVoiceOS/ovos-backend-manager`

## Configuration

edit `~/.config/mycroft/ovos_backend_manager.conf`

```javascript
{
    "server": {
        "url": "http://XXX.XXX.XXX.XX:6712",
        "version": "v1",
        "admin_key": "XXXX"
    }
}
```

## Usage

`ovos-backend-manager` will be available in the command line after installing

