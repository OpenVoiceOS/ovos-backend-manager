import json
import os

from cutecharts.charts import Pie
from ovos_local_backend.database.metrics import JsonMetricDatabase
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.database.utterances import JsonUtteranceDatabase
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase
from pywebio.input import actions
from pywebio.output import put_text, popup, put_code, put_markdown, put_html, use_scope


def device_select(back_handler=None):
    devices = {uuid: f"{device['name']}@{device['device_location']}"
               for uuid, device in DeviceDatabase().items()}
    buttons = [{'label': "All Devices", 'value': "all"}] + \
              [{'label': d, 'value': uuid} for uuid, d in devices.items()]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    if devices:
        uuid = actions(label="What device would you like to inspect?",
                       buttons=buttons)
        if uuid == "main":
            metrics_menu(back_handler=back_handler)
            return
        else:
            if uuid == "all":
                uuid = None
            metrics_select(uuid=uuid, back_handler=back_handler)
    else:
        popup("No devices paired yet!")
        metrics_menu(back_handler)


def metrics_select(back_handler=None, uuid=None):
    buttons = []
    db = JsonMetricDatabase()
    if not len(db):
        with use_scope("charts", clear=True):
            put_text("No metrics uploaded yet!")
        metrics_menu(back_handler=back_handler)
        return

    for m in db:
        name = f"{m['metric_id']}-{m['metric_type']}"
        if uuid is not None and m["uuid"] != uuid:
            continue
        buttons.append({'label': name, 'value': m['metric_id']})
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})
    opt = actions(label="Select a metric to inspect",
                  buttons=buttons)
    if opt == "main":
        device_select(back_handler=back_handler)
        return
    # id == db_position + 1
    with use_scope("charts", clear=True):
        put_markdown("# Metadata")
        put_code(json.dumps(db[opt - 1], indent=4), "json")
    metrics_select(back_handler=back_handler)


def metrics_menu(back_handler=None):
    buttons = [{'label': 'Metric Types', 'value': "types"},
               {'label': 'Intents', 'value': "intents"},
               {'label': 'FallbackSkill', 'value': "fallback"},
               {'label': 'STT', 'value': "stt"},
               {'label': 'TTS', 'value': "tts"},
               {'label': 'Open Dataset', 'value': "opt-in"},
               {'label': 'Inspect Device Metrics', 'value': "metrics"},
               {'label': 'Delete metrics database', 'value': "delete_metrics"}
               ]
    if back_handler:
        buttons.insert(0, {'label': '<- Go Back', 'value': "main"})

    opt = actions(label="What would you like to do?",
                  buttons=buttons)
    m = MetricsReportGenerator()
    if opt == "opt-in":
        with use_scope("charts", clear=True):
            put_markdown(f"""
        # Open Dataset Report

        Total Registered Devices: {len(DeviceDatabase())}
        Currently Opted-in: {len([d for d in DeviceDatabase() if d.opt_in])}
        Unique Devices seen: {m.total_devices}
        
        Total Metrics submitted: {len(JsonMetricDatabase())}
        Total WakeWords submitted: {len(JsonWakeWordDatabase())} 
        Total Utterances submitted: {len(JsonUtteranceDatabase())} 
        """)
            put_html(m.uploads_chart().render_notebook())

    if opt == "intents":
        with use_scope("charts", clear=True):
            put_markdown(f"""
                    # Intent Matches Report

                    Total queries: {m.total_intents + m.total_fallbacks}
                    Total Intents: {m.total_intents}
                    """)
            put_html(m.intent_type_chart().render_notebook())
    if opt == "stt":
        with use_scope("charts", clear=True):
            put_html(m.stt_type_chart().render_notebook())
    if opt == "tts":
        with use_scope("charts", clear=True):
            put_html(m.tts_type_chart().render_notebook())
    if opt == "types":
        with use_scope("charts", clear=True):
            put_markdown(f"""
        # Metrics Report
        
        Total Intents: {m.total_intents}
        Total Fallbacks: {m.total_fallbacks}
        Total Transcriptions: {m.total_stt}
        Total TTS: {m.total_tts}
        """)
            put_html(m.metrics_type_chart().render_notebook())
    if opt == "fallback":
        with use_scope("charts", clear=True):
            f = 0
            if m.total_intents + m.total_fallbacks > 0:
                f = m.total_intents / (m.total_intents + m.total_fallbacks)
            put_markdown(f"""
                        # Fallback Matches Report

                        Total queries: {m.total_intents + m.total_fallbacks}
                        Total Intents: {m.total_intents}
                        Total Fallbacks: {m.total_fallbacks}

                        Failure Percentage: {1 - f}
                        """)
            put_html(m.fallback_type_chart().render_notebook())
    if opt == "metrics":
        device_select(back_handler=back_handler)
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
            metrics_menu(back_handler=back_handler)
        return
    if opt == "main":
        with use_scope("charts", clear=True):
            back_handler()
        return
    metrics_menu(back_handler=back_handler)


class MetricsReportGenerator:
    def __init__(self):
        self.total_intents = 0
        self.total_fallbacks = 0
        self.total_stt = 0
        self.total_tts = 0
        self.total_ww = len(JsonWakeWordDatabase())
        self.total_utt = len(JsonUtteranceDatabase())
        self.total_devices = len(DeviceDatabase())

        self.intents = {}
        self.fallbacks = {}
        self.tts = {}
        self.stt = {}
        self.load_metrics()

    def uploads_chart(self):
        chart = Pie("Uploaded Data")
        chart.set_options(
            labels=["wake-words", "utterances"],
            inner_radius=0,
        )
        chart.add_series([self.total_ww, self.total_utt])
        return chart

    def metrics_type_chart(self):
        chart = Pie("Metric Types")
        chart.set_options(
            labels=["intents", "fallbacks", "stt", "tts"],
            inner_radius=0,
        )
        chart.add_series([self.total_intents,
                          self.total_fallbacks,
                          self.total_stt,
                          self.total_tts])
        return chart

    def intent_type_chart(self):
        chart = Pie("Intent Matches")
        chart.set_options(
            labels=list(self.intents.keys()),
            inner_radius=0,
        )
        chart.add_series(list(self.intents.values()))
        return chart

    def fallback_type_chart(self):
        chart = Pie("Fallback Skills")
        chart.set_options(
            labels=list(self.fallbacks.keys()),
            inner_radius=0,
        )
        chart.add_series(list(self.fallbacks.values()))
        return chart

    def tts_type_chart(self):
        chart = Pie("Text To Speech Engines")
        chart.set_options(
            labels=list(self.tts.keys()),
            inner_radius=0,
        )
        chart.add_series(list(self.tts.values()))
        return chart

    def stt_type_chart(self):
        chart = Pie("Speech To Text Engines")
        chart.set_options(
            labels=list(self.stt.keys()),
            inner_radius=0,
        )
        chart.add_series(list(self.stt.values()))
        return chart

    def load_metrics(self):
        self.total_intents = 0
        self.total_fallbacks = 0
        self.total_stt = 0
        self.total_tts = 0
        self.total_ww = len(JsonWakeWordDatabase())
        self.total_devices = 0

        self.intents = {}
        self.fallbacks = {}
        self.tts = {}
        self.stt = {}

        db = JsonMetricDatabase()
        devs = []
        for m in db:
            if m["uuid"] not in devs:
                devs.append(m["uuid"])
                self.total_devices += 1
            if m["metric_type"] == "intent_service":
                self.total_intents += 1
                k = f"{m['meta']['intent_type']}"
                if k not in self.intents:
                    self.intents[k] = 0
                self.intents[k] += 1
            if m["metric_type"] == "fallback_handler":
                self.total_fallbacks += 1
                k = f"{m['meta']['handler']}"
                if m['meta'].get("skill_id"):
                    k = f"{m['meta']['skill_id']}:{m['meta']['handler']}"
                if k not in self.fallbacks:
                    self.fallbacks[k] = 0
                self.fallbacks[k] += 1
            if m["metric_type"] == "stt":
                self.total_stt += 1
                k = f"{m['meta']['stt']}"
                if k not in self.stt:
                    self.stt[k] = 0
                self.stt[k] += 1
            if m["metric_type"] == "speech":
                self.total_tts += 1
                k = f"{m['meta']['tts']}"
                if k not in self.tts:
                    self.tts[k] = 0
                self.tts[k] += 1
