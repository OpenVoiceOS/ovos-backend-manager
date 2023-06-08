import json
import os
import time
from base64 import b64encode

from pywebio.input import actions, file_upload, input_group, textarea, select
from pywebio.output import put_text, put_code, use_scope, put_markdown, popup, put_image, put_file, put_html, \
    put_buttons, put_table

from ovos_backend_manager.configuration import DB


def _render_ww(rec_id):

    def on_tag(bt):
        data["tag"] = bt
        DB.update_ww_recording(rec_id, tag=bt)
        _render_ww(rec_id)

    with use_scope("main_view", clear=True):
        data = DB.get_ww_recording(rec_id)
        data["tag"] = data.get("tag") or "untagged"

        # TODO - get binary_data directly
        if os.path.isfile(data["path"]):
            content = open(data["path"], 'rb').read()
            html = f"""
            <audio controls src="data:audio/x-wav;base64,{b64encode(content).decode('ascii')}" />
            """
            put_table([
                ['metadata', put_code(json.dumps(data, indent=4), "json")],
                ['playback', put_html(html)],
                ['file', put_file(data["path"].split("/")[-1], content, 'Download')],
                ['classify', put_buttons(["wake_word", "speech", "noise", "silence"],
                                         onclick=on_tag)]
            ])

        else:
            put_table([
                ['metadata', put_code(json.dumps(data, indent=4), "json")],
                ['playback', put_markdown("**WARNING** - file not found")],
                ['file', put_markdown("**WARNING** - file not found")],
                ['classify', put_buttons(["untagged", "wake_word", "speech", "noise", "silence"],
                                         onclick=on_tag)]
            ])


def ww_select(back_handler=None, uuid=None, ww=None):
    buttons = []
    if not len(DB.list_ww_recordings()):
        with use_scope("main_view", clear=True):
            put_text("No wake words uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in DB.list_ww_recordings():
        if uuid is not None and m["uuid"] != uuid:
            continue
        if ww is not None and m["transcription"] != ww:
            continue
        name = f"{m['recording_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['recording_id']})

    if len(buttons) == 0:
        with use_scope("main_view", clear=True):
            put_text("No wake words uploaded from this device yet!")
        ww_menu(back_handler=back_handler)
        return

    elif back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    rec_id = actions(label="Select a WakeWord recording", buttons=buttons)

    if rec_id == "main":  # go back
        ww_menu(back_handler=back_handler)
    else:
        _render_ww(rec_id)
        ww_select(back_handler=back_handler, ww=ww, uuid=uuid)


def utt_select(back_handler=None, uuid=None, utt=None):
    buttons = []
    if not len(DB.list_stt_recordings()):
        with use_scope("main_view", clear=True):
            put_text("No utterances uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in DB.list_stt_recordings():
        if uuid is not None and m["uuid"] != uuid:
            continue
        if utt is not None and m["transcription"] != utt:
            continue
        name = f"{m['recording_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['recording_id']})

    if len(buttons) == 0:
        with use_scope("main_view", clear=True):
            put_text("No utterances uploaded from this device yet!")
        utt_menu(back_handler=back_handler)
        return
    else:
        if back_handler:
            buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
        rec_id = actions(label="Select a Utterance recording",
                         buttons=buttons)
        if rec_id == "main":
            utt_menu(back_handler=back_handler)
            return

    with use_scope("main_view", clear=True):
        # opt is recording_id
        data = DB.get_stt_recording(rec_id)
        put_code(json.dumps(data, indent=4), "json")
        # TODO - get binary data from api
        if os.path.isfile(data["path"]):
            content = open(data["path"], 'rb').read()
            html = f"""<audio controls src="data:audio/x-wav;base64,{b64encode(content).decode('ascii')}" />"""
            put_html(html)
            put_file(data["path"].split("/")[-1], content, 'Download Audio')
        else:
            put_markdown("**WARNING** - audio file not found")

    utt_select(back_handler=back_handler, uuid=uuid, utt=utt)


def device_select(back_handler=None, ww=True):
    devices = {device["uuid"]: f"{device['name']}@{device['device_location']}"
               for device in DB.list_devices()}
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
        with use_scope("main_view", clear=True):
            put_text("No devices paired yet!")
        if ww:
            ww_menu(back_handler=back_handler)
        else:
            utt_menu(back_handler=back_handler)


def ww_opts(back_handler=None, uuid=None):
    wws = list(set([ww["transcription"] for ww in DB.list_ww_recordings()]))
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
        with use_scope("main_view", clear=True):
            put_text("No wake words uploaded yet!")
        ww_menu(back_handler=back_handler)


def utt_opts(back_handler=None, uuid=None):
    utts = list(set([ww["transcription"] for ww in DB.list_stt_recordings()]))
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
        with use_scope("main_view", clear=True):
            put_text("No recordings uploaded yet!")
        utt_menu(back_handler=back_handler)


def _render_ww_tagger(selected_idx, selected_wws, untagged_only=False):
    def on_tag(tag):
        nonlocal selected_idx, selected_wws

        if all((ww.get("tag") != "untagged" for ww in selected_wws)):
            if untagged_only:
                popup("No more wake words to tag!")
                return

        if tag == "Skip ->":
            selected_idx += 1
            if selected_idx >= len(selected_wws):
                selected_idx = 0
            if untagged_only and selected_wws[selected_idx]["tag"] != "untagged":
                return on_tag(tag)  # recurse

        elif selected_idx is not None:
            db_id = selected_wws[selected_idx]["recording_id"]
            DB.update_ww_recording(db_id, tag=tag)

        _render_ww_tagger(selected_idx, selected_wws, untagged_only=untagged_only)

    def on_gender(tag):
        nonlocal selected_idx, selected_wws

        if selected_idx is not None:
            db_id = selected_wws[selected_idx]["recording_id"]
            DB.update_ww_recording(db_id, speaker_type=tag)

        _render_ww_tagger(selected_idx, selected_wws, untagged_only=untagged_only)

    with use_scope("main_view", clear=True):
        content = open(selected_wws[selected_idx]["path"], 'rb').read()
        html = f"""
        <audio controls src="data:audio/x-wav;base64,{b64encode(content).decode('ascii')}" />
        """

        put_table([
            ['wake word', selected_wws[selected_idx]["transcription"]],
            ['metadata', put_code(
                json.dumps(selected_wws[selected_idx], indent=4), "json")],
            ['playback', put_html(html)],
            ['speaker type', put_buttons(["male", "female", "children"],
                                         onclick=on_gender)],
            ['tag', put_buttons(["wake_word", "speech", "noise", "silence", "Skip ->"],
                                onclick=on_tag)],
        ])


def ww_tagger(back_handler=None, selected_wws=None, selected_idx=None, untagged_only=True):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/wakewords.png', 'rb').read()
        put_image(img)

    def get_next_untagged():
        nonlocal selected_idx
        if untagged_only:
            for idx, ww in enumerate(selected_wws):
                if ww.get("tag", "untagged") == "untagged":
                    selected_idx = idx
                    break
            else:
                selected_idx = 0

    if not selected_wws:
        wws = set([w["transcription"] for w in DB.list_ww_recordings()
                   if os.path.isfile(w["path"])])
        if not len(wws):
            with use_scope("main_view", clear=True):
                put_text("No wake words uploaded yet!")
            datasets_menu(back_handler=back_handler)
            return
        current_ww = select("Target WW", wws)
        selected_wws = [w for w in DB.list_ww_recordings()
                        if w["transcription"] == current_ww
                        and os.path.isfile(w["path"])]
        selected_idx = 0
    else:
        selected_idx = selected_idx or 0
        current_ww = selected_wws[selected_idx]["transcription"]
        if untagged_only:
            get_next_untagged()

    # add "untagged" tag if needed
    for idx, ww in enumerate(selected_wws):
        if "tag" not in ww:
            selected_wws[idx]["tag"] = "untagged"
        if "speaker_type" not in ww:
            selected_wws[idx]["speaker_type"] = "untagged"

    _render_ww_tagger(selected_idx, selected_wws, untagged_only)

    buttons = [
        {'label': "Show all recordings" if untagged_only else 'Show untagged only', 'value': "toggle"},
        {'label': f'Delete {current_ww} database', 'value': "delete_ww"}
    ]

    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)

    if opt == "toggle":
        untagged_only = not untagged_only
        get_next_untagged()

    if opt == "delete_ww":
        with use_scope("main_view", clear=True):
            put_markdown(f"""Are you sure you want to delete the {current_ww} wake word database?
            **this can not be undone**, proceed with caution!
            **ALL** {current_ww} recordings will be **lost**""")
        opt = actions(label=f"Delete {current_ww} database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:

            for ww in selected_wws:
                if os.path.isfile(ww["path"]):
                    os.remove(ww["path"])

                rec_id = current_ww  # TODO - rec_id
                DB.delete_ww_recording(rec_id)

            with use_scope("main_view", clear=True):
                put_text(f"{current_ww} database deleted!")
        ww_tagger(back_handler=back_handler, untagged_only=untagged_only)
        return

    if opt == "main":
        with use_scope("main_view", clear=True):
            datasets_menu(back_handler=back_handler)
        return
    ww_tagger(back_handler=back_handler,
              selected_idx=selected_idx,
              selected_wws=selected_wws,
              untagged_only=untagged_only)


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
        with use_scope("main_view", clear=True):
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

            else:
                uuid = "AnonDevice"  # TODO - allow tagging to a device

                meta = {
                    "transcription": name,
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
                rec = DB.add_ww_recording(byte_data=content, transcription=name, metadata=meta)

                with popup("wake word uploaded!"):
                    put_code(json.dumps(meta, indent=4), "json")

    if opt == "delete_ww":
        with use_scope("main_view", clear=True):
            put_markdown("""Are you sure you want to delete the wake word database?
            **this can not be undone**, proceed with caution!
            **ALL** wake word recordings will be **lost**""")
        opt = actions(label="Delete wake words database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:

            for rec in DB.list_ww_recordings():
                DB.delete_ww_recording(rec_id=rec["recording_id"])

            with use_scope("main_view", clear=True):
                put_text("wake word database deleted!")

        datasets_menu(back_handler=back_handler)
        return
    if opt == "main":
        with use_scope("main_view", clear=True):
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
        with use_scope("main_view", clear=True):
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
                uuid = "AnonDevice"  # TODO - allow tagging to a device

                meta = {
                    "transcription": utterance,
                    "uuid": uuid
                }
                DB.add_stt_recording(content, utterance, meta)

                with popup("utterance recording uploaded!"):
                    put_code(json.dumps(meta, indent=4), "json")

    if opt == "delete_utt":
        with use_scope("main_view", clear=True):
            put_markdown("""Are you sure you want to delete the utterances database?
                        **this can not be undone**, proceed with caution!
                        **ALL** utterance recordings will be **lost**""")
        opt = actions(label="Delete utterances database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:

            for rec in DB.list_stt_recordings():
                DB.delete_stt_recording(rec["recording_id"])

            with use_scope("main_view", clear=True):
                put_text("utterance database deleted!")
        datasets_menu(back_handler=back_handler)
        return
    if opt == "main":
        with use_scope("main_view", clear=True):
            datasets_menu(back_handler=back_handler)
        return

    utt_menu(back_handler=back_handler)


def datasets_menu(back_handler=None):
    with use_scope("logo", clear=True):
        img = open(f'{os.path.dirname(__file__)}/res/open_dataset.png', 'rb').read()
        put_image(img)

    buttons = [
        {'label': 'Tag Wake Words', 'value': "dataset"},
        {'label': 'Manage Wake Words', 'value': "ww"},
        {'label': 'Manage Utterance Recordings', 'value': "utt"},
    ]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)

    if opt == "dataset":
        ww_tagger(back_handler=back_handler)
    elif opt == "utt":
        utt_menu(back_handler=back_handler)
    elif opt == "ww":
        ww_menu(back_handler=back_handler)
    elif opt == "main":
        with use_scope("main_view", clear=True):
            if back_handler:
                back_handler()
        return
    datasets_menu(back_handler=back_handler)
