import random

from ovos_local_backend.database.metrics import JsonMetricDatabase
from ovos_local_backend.database.settings import DeviceDatabase
from ovos_local_backend.database.utterances import JsonUtteranceDatabase
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase

mk1_icon = "https://market.mycroft.ai/assets/mark-1-icon.svg"
mk2_icon = "https://market.mycroft.ai/assets/mark-2-icon.svg"
picroft_icon = "https://market.mycroft.ai/assets/picroft-icon.svg"
ovos_icon = "https://github.com/OpenVoiceOS/ovos_assets/raw/master/Logo/ovos-logo-512.png"
ocp_icon = "https://github.com/OpenVoiceOS/ovos-ocp-audio-plugin/raw/dev/ovos_plugin_common_play/ocp/res/desktop/OCP.png"
kde_icon = "https://home.mycroft.ai/assets/kde-icon.svg"
generic = "https://home.mycroft.ai/assets/generic-device-icon-white.svg"


def get_device_list():
    return {uuid: f"{device['name']}@{device['device_location']}"
            for uuid, device in DeviceDatabase().items()}


def get_metrics_list():
    db = JsonMetricDatabase()
    for m in db:
        print(m)


def get_ww_list():
    wws = {}
    db = JsonWakeWordDatabase()
    for m in db:
        wws[m["wakeword_id"]] = {"name": m["transcription"], }
        print(m)


def get_utt_list():
    db = JsonUtteranceDatabase()
    for m in db:
        print(m)


def create_mock_dbs(utts=True, ww=False, metrics=True):
    import time

    if utts:
        with JsonUtteranceDatabase() as db:
            for i in range(0, 10):
                db.add_utterance(f"number {i}", f"/tmp/number{i}.mp3", random.randint(100, 105))
            db.add_utterance("hello world", "/tmp/hello.mp3", random.randint(100, 105))

    if ww:
        with JsonWakeWordDatabase() as db:
            for i in range(0, 5):
                meta = {"name": "hey mycroft",
                        "time": time.time(),
                        "accountId": "0",
                        "sessionId": random.randint(100, 105),
                        "model": "5223842df0cdee5bca3eff8eac1b67fc",
                        "engine": "0f4df281688583e010c26831abdc2222"}
                db.add_wakeword(f"hey mycroft", f"/tmp/hey_mycroft_{i}.mp3", meta,
                                uuid=random.randint(100, 105))
            for i in range(0, 5):
                meta = {"name": "hey neon",
                        "time": time.time(),
                        "accountId": "0",
                        "sessionId": random.randint(100, 105),
                        "model": "5223842df0c35gweb67fc",
                        "engine": "0f4d24rgtebyhe568583e010c26831abdc2222"}
                db.add_wakeword(f"hey neon", f"/tmp/hey_neon_{i}.mp3", meta,
                                uuid=random.randint(100, 105))
            for i in range(0, 5):
                meta = {"name": "hey ezra",
                        "time": time.time(),
                        "accountId": "0",
                        "sessionId": random.randint(100, 105),
                        "model": "522384sgdshhqe5bca3eff8eac1b67fc",
                        "engine": "0f4dsdgage010c26831abdc2222"}
                db.add_wakeword(f"hey ezra", f"/tmp/hey_ezra_{i}.mp3", meta,
                                uuid=random.randint(100, 105))

    if metrics:
        with JsonMetricDatabase() as db:
            for i in range(0, 5):
                uuid = random.randint(100, 105)
                name = f"execute order {random.randint(1, 100)}"
                start = time.time()
                end = start + random.randint(10, 89999999)
                metric = {"start_time": start, "time": end, "id": uuid,
                          "transcription": name, "stt": f"FakeSTTEngine{random.randint(1, 3)}"}
                db.add_metric(f"stt", metric, uuid)

            for i in range(0, 3):
                uuid = random.randint(100, 105)
                name = f"my_intent_{random.randint(1, 6)}"
                start = time.time()
                end = start + random.randint(10, 89999999)
                metric = {"start_time": start, "time": end, "id": uuid,
                          "intent_type": name}
                db.add_metric(f"intent_service", metric, uuid)

            for i in range(0, 3):
                uuid = random.randint(100, 105)
                name = f"fallback_handler_{random.randint(1, 5)}"
                start = time.time()
                end = start + random.randint(10, 89999999)
                metric = {"start_time": start, "time": end, "id": uuid,
                          "handler": name, "skill_id": f"my_skill_{i}.author"}
                db.add_metric(f"fallback_handler", metric, uuid)

            for i in range(0, 3):
                uuid = random.randint(100, 105)
                name = f"this is test number {random.randint(1, 100)}"
                start = time.time()
                end = start + random.randint(10, 89999999)
                metric = {"start_time": start, "time": end, "id": uuid,
                          "utterance": name, "tts": f"FakeTTSEngine{random.randint(1, 3)}"}
                db.add_metric(f"speech", metric, uuid)


if __name__ == "__main__":
    create_mock_dbs()

    # get_metrics_list()
    get_ww_list()
    # get_utt_list()
