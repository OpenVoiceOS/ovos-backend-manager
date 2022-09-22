import json
import os
import time

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.database.utterances import JsonUtteranceDatabase
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase
from pywebio.input import actions, file_upload, input_group, textarea
from pywebio.output import put_text, put_code, use_scope, put_markdown, popup, put_image


def ww_select(back_handler=None, uuid=None, ww=None):
    buttons = []
    db = JsonWakeWordDatabase()
    if not len(db):
        with use_scope("datasets", clear=True):
            put_text("No wake words uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in db:
        if uuid is not None and m["uuid"] != uuid:
            continue
        if ww is not None and m["transcription"] != ww:
            continue
        name = f"{m['wakeword_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['wakeword_id']})

    if len(buttons) == 0:
        with use_scope("datasets", clear=True):
            put_text("No wake words uploaded from this device yet!")
        opt = "main"
    else:
        if back_handler:
            buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
        opt = actions(label="Select a WakeWord recording",
                      buttons=buttons)
    if opt == "main":
        ww_menu(back_handler=back_handler)
        return
    # id == db_position + 1
    with use_scope("datasets", clear=True):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    ww_select(back_handler=back_handler, ww=ww, uuid=uuid)


def utt_select(back_handler=None, uuid=None, utt=None):
    buttons = []
    db = JsonUtteranceDatabase()
    if not len(db):
        with use_scope("datasets", clear=True):
            put_text("No utterances uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in db:
        if uuid is not None and m["uuid"] != uuid:
            continue
        if utt is not None and m["transcription"] != utt:
            continue
        name = f"{m['utterance_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['utterance_id']})

    if len(buttons) == 0:
        with use_scope("datasets", clear=True):
            put_text("No utterances uploaded from this device yet!")
        opt = "main"
    else:
        if back_handler:
            buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
        opt = actions(label="Select a Utterance recording",
                      buttons=buttons)
    if opt == "main":
        utt_menu(back_handler=back_handler)
        return

    # id == db_position + 1
    with use_scope("datasets", clear=True):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    utt_select(back_handler=back_handler, uuid=uuid, utt=utt)


def device_select(back_handler=None, ww=True):
    devices = {uuid: f"{device['name']}@{device['device_location']}"
               for uuid, device in DeviceDatabase().items()}
    buttons = [{'label': "All Devices", 'value': "all"},
               {'label': "Unknown Devices", 'value': "AnonDevice"}] + \
              [{'label': d, 'value': uuid} for uuid, d in devices.items()]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if devices:
        uuid = actions(label="What device would you like to inspect?",
                       buttons=buttons)
        if uuid == "main":
            datasets_menu(back_handler=back_handler)
            return
        else:
            if uuid == "all":
                uuid = None
            if ww:
                ww_select(uuid=uuid, back_handler=back_handler)
            else:
                utt_select(uuid=uuid, back_handler=back_handler)
    else:
        with use_scope("datasets", clear=True):
            put_text("No devices paired yet!")
        if ww:
            ww_menu(back_handler=back_handler)
        else:
            utt_menu(back_handler=back_handler)


def ww_opts(back_handler=None, uuid=None):
    wws = list(set([ww["transcription"] for ww in JsonWakeWordDatabase()]))
    buttons = [{'label': "All Wake Words", 'value': "all"}] + \
              [{'label': ww, 'value': ww} for ww in wws]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if wws:
        ww = actions(label="What wake word would you like to inspect?", buttons=buttons)
        if ww == "main":
            datasets_menu(back_handler=back_handler)
            return
        if ww == "all":
            ww = None
        ww_select(ww=ww, back_handler=back_handler, uuid=uuid)
    else:
        with use_scope("datasets", clear=True):
            put_text("No wake words uploaded yet!")
        ww_menu(back_handler=back_handler)


def utt_opts(back_handler=None, uuid=None):
    utts = list(set([ww["transcription"] for ww in JsonUtteranceDatabase()]))
    buttons = [{'label': "All Utterances", 'value': "all"}] + \
              [{'label': ww, 'value': ww} for ww in utts]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if utts:
        utt = actions(label="What utterance would you like to inspect?", buttons=buttons)
        if utt == "main":
            datasets_menu(back_handler=back_handler)
            return
        if utt == "all":
            utt = None
        utt_select(utt=utt, back_handler=back_handler, uuid=uuid)
    else:
        with use_scope("datasets", clear=True):
            put_text("No recordings uploaded yet!")
        utt_menu(back_handler=back_handler)


def ww_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/wakewords.png', 'rb').read()
        put_image(img)

    buttons = [{'label': 'Inspect Devices', 'value': "dev"},
               {'label': 'Inspect Wake Words', 'value': "ww"},
               {'label': 'Upload Wake Word', 'value': "upload"},
               {'label': 'Delete wake words database', 'value': "delete_ww"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)
    if opt == "dev":
        device_select(back_handler=back_handler, ww=True)
    if opt == "ww":
        ww_opts(back_handler=back_handler)
    if opt == "upload":
        with use_scope("datasets", clear=True):
            data = input_group("Upload wake word", [
                textarea("wake word name", placeholder="hey mycroft", required=True, name="name"),
                file_upload("wake word recording", name="file")
            ])

            name = data["name"]
            filename = data["file"]["filename"]
            mime = data["file"]["mime_type"]
            content = data["file"]["content"]
            if mime != "audio/x-wav":
                popup("invalid format!")
            # if mime in ["application/json"]:
            else:
                os.makedirs(f"{CONFIGURATION['data_path']}/wakewords", exist_ok=True)

                uuid = "AnonDevice"  # TODO - allow tagging to a device
                wav_path = f"{CONFIGURATION['data_path']}/wakewords/{name}.{filename}"
                meta_path = f"{CONFIGURATION['data_path']}/wakewords/{name}.{filename}.meta"
                meta = {
                    "transcription": name,
                    "path": wav_path,
                    "meta": {
                        "name": name,
                        "time": time.time(),
                        "accountId": "0",
                        "sessionId": "0",
                        "model": "uploaded_file",
                        "engine": "uploaded_file"
                    },
                    "uuid": uuid
                }
                with JsonWakeWordDatabase() as db:
                    db.add_wakeword(name, wav_path, meta, uuid)
                with open(wav_path, "wb") as f:
                    f.write(content)
                with open(meta_path, "w") as f:
                    json.dump(meta, f)
                with popup("wake word uploaded!"):
                    put_code(json.dumps(meta, indent=4), "json")

    if opt == "delete_ww":
        with use_scope("datasets", clear=True):
            put_markdown("""Are you sure you want to delete the wake word database?
            **this can not be undone**, proceed with caution!
            **ALL** wake word recordings will be **lost**""")
        opt = actions(label="Delete wake words database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            # TODO - also remove files from path
            os.remove(JsonWakeWordDatabase().db.path)
            with use_scope("datasets", clear=True):
                put_text("wake word database deleted!")
        datasets_menu(back_handler=back_handler)
        return
    if opt == "main":
        with use_scope("datasets", clear=True):
            datasets_menu(back_handler=back_handler)
        return
    ww_menu(back_handler=back_handler)


def utt_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/utterances.png', 'rb').read()
        put_image(img)

    buttons = [{'label': 'Inspect Devices', 'value': "dev"},
               {'label': 'Inspect Recordings', 'value': "utt"},
               {'label': 'Upload Utterance', 'value': "upload"},
               {'label': 'Delete utterances database', 'value': "delete_utt"}]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)
    if opt == "dev":
        device_select(back_handler=back_handler, ww=False)
    if opt == "utt":
        utt_opts(back_handler=back_handler)
    if opt == "upload":
        with use_scope("datasets", clear=True):
            data = input_group("Upload utterance", [
                textarea("transcript", placeholder="hello world", required=True, name="utterance"),
                file_upload("speech recording", name="file")
            ])

            utterance = data["utterance"]
            filename = data["file"]["filename"]
            mime = data["file"]["mime_type"]
            content = data["file"]["content"]
            if mime != "audio/x-wav":
                popup("invalid format!")
            # if mime in ["application/json"]:
            else:
                os.makedirs(f"{CONFIGURATION['data_path']}/utterances", exist_ok=True)

                uuid = "AnonDevice"  # TODO - allow tagging to a device
                path = f"{CONFIGURATION['data_path']}/utterances/{utterance}.{filename}"

                meta = {
                    "transcription": utterance,
                    "path": path,
                    "uuid": uuid
                }
                with JsonUtteranceDatabase() as db:
                    db.add_utterance(utterance, path, uuid)

                with open(path, "wb") as f:
                    f.write(content)

                with popup("utterance recording uploaded!"):
                    put_code(json.dumps(meta, indent=4), "json")

    if opt == "delete_utt":
        with use_scope("datasets", clear=True):
            put_markdown("""Are you sure you want to delete the utterances database?
                        **this can not be undone**, proceed with caution!
                        **ALL** utterance recordings will be **lost**""")
        opt = actions(label="Delete utterances database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            # TODO - also remove files from path
            os.remove(JsonUtteranceDatabase().db.path)
            with use_scope("datasets", clear=True):
                put_text("utterance database deleted!")
        datasets_menu(back_handler=back_handler)
        return
    if opt == "main":
        with use_scope("datasets", clear=True):
            datasets_menu(back_handler=back_handler)
        return

    utt_menu(back_handler=back_handler)


def datasets_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/open_dataset.png', 'rb').read()
        put_image(img)

    buttons = [{'label': 'Wake Words', 'value': "ww"},
               {'label': 'Utterance Recordings', 'value': "utt"}
               ]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)

    if opt == "utt":
        utt_menu(back_handler=back_handler)
    if opt == "ww":
        ww_menu(back_handler=back_handler)
    if opt == "main":
        with use_scope("datasets", clear=True):
            back_handler()
        return
    datasets_menu(back_handler=back_handler)
