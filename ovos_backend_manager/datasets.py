import json
import os

from ovos_local_backend.database.metrics import JsonMetricDatabase
from ovos_local_backend.database.utterances import JsonUtteranceDatabase
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase
from pywebio.input import actions
from pywebio.output import put_text, popup, put_code


def metrics_select(back_handler=None):
    buttons = []
    db = JsonMetricDatabase()
    if not len(db):
        popup("No metrics uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in db:
        name = f"{m['metric_id']}-{m['metric_type']}"
        buttons.append({'label': name, 'value': m['metric_id']})
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a metric to inspect",
                  buttons=buttons)
    if opt == "main":
        datasets_menu(back_handler=back_handler)
        return
    # id == db_position + 1
    name = f"{opt}-{db[opt - 1]['metric_type']}"
    with popup(name):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    metrics_select()


def ww_select(back_handler=None):
    buttons = []
    db = JsonWakeWordDatabase()
    if not len(db):
        popup("No wake words uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in db:
        name = f"{m['wakeword_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['wakeword_id']})
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a WakeWord recording",
                  buttons=buttons)
    if opt == "main":
        datasets_menu(back_handler=back_handler)
        return
    # id == db_position + 1
    name = f"{opt}-{db[opt - 1]['transcription']}"
    with popup(name):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    ww_select()


def utt_select(back_handler=None):
    buttons = []
    db = JsonUtteranceDatabase()
    if not len(db):
        popup("No utterances uploaded yet!")
        datasets_menu(back_handler=back_handler)
        return

    for m in db:
        name = f"{m['utterance_id']}-{m['transcription']}"
        buttons.append({'label': name, 'value': m['utterance_id']})
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a Utterance recording",
                  buttons=buttons)
    if opt == "main":
        datasets_menu(back_handler=back_handler)
        return

    # id == db_position + 1
    name = f"{opt}-{db[opt - 1]['transcription']}"
    with popup(name):
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    utt_select()


def datasets_menu(back_handler=None):
    buttons = [{'label': 'View Metrics', 'value': "metrics"},
               {'label': 'View Wake Words', 'value': "ww"},
               {'label': 'View Utterances', 'value': "utt"},
               {'label': 'Delete metrics database', 'value': "delete_metrics"},
               {'label': 'Delete wake words database', 'value': "delete_ww"},
               {'label': 'Delete utterances database', 'value': "delete_utts"}
               ]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)

    if opt == "metrics":
        metrics_select(back_handler=back_handler)
    if opt == "ww":
        ww_select(back_handler=back_handler)
    if opt == "utt":
        utt_select(back_handler=back_handler)
    if opt == "delete_metrics":
        with popup("Are you sure you want to delete the metrics database?"):
            put_text("this can not be undone, proceed with caution!")
            put_text("ALL metrics will be lost")
        opt = actions(label="Delete metrics database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            os.remove(JsonMetricDatabase().db.path)
            back_handler()
        else:
            datasets_menu(back_handler=back_handler)
        return
    if opt == "delete_ww":
        with popup("Are you sure you want to delete the wake word database?"):
            put_text("this can not be undone, proceed with caution!")
            put_text("ALL wake word recordings will be lost")
        opt = actions(label="Delete wake words database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            # TODO - also remove files from path
            os.remove(JsonWakeWordDatabase().db.path)
            back_handler()
        else:
            datasets_menu(back_handler=back_handler)
        return
    if opt == "delete_utts":
        with popup("Are you sure you want to delete the utterance database?"):
            put_text("this can not be undone, proceed with caution!")
            put_text("ALL utterance recordings will be lost")
        opt = actions(label="Delete utterance recordings database?",
                      buttons=[{'label': "yes", 'value': True},
                               {'label': "no", 'value': False}])
        if opt:
            # TODO - also remove files from path
            os.remove(JsonUtteranceDatabase().db.path)
            back_handler()
        else:
            datasets_menu(back_handler=back_handler)
        return
    if opt == "main":
        back_handler()
        return
    datasets_menu(back_handler=back_handler)
