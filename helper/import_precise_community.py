import os
import random

from ovos_local_backend.configuration import CONFIGURATION
from ovos_local_backend.database.metrics import JsonMetricDatabase, Metric
from ovos_local_backend.database.wakewords import JsonWakeWordDatabase, WakeWordRecording
from os.path import dirname
from os import listdir


def import_ww(ww, lang):
    from uuid import uuid4
    import time

    path = f"{dirname(__file__)}/Precise-Community-Data/{ww}/{lang}"
    with JsonWakeWordDatabase() as db:
        for f in listdir(path):
            meta = {"name": ww.replace("hey", "hey "),
                    "time": time.time(),
                    "accountId": "0",
                    "sessionId": str(uuid4()),
                    "model": "precise-community-data",
                    "engine": "precise-community-data"}
            db.add_wakeword(ww,
                            path=f"{path}/{f}",
                            meta=meta,
                            uuid=str(uuid4()))


if __name__ == "__main__":
    import_ww("amelia", "en")
    import_ww("athena", "en")
    import_ww("computer", "en")
    import_ww("heycomputer", "en")
    import_ww("heysavant", "wake-word/en")
    import_ww("heychatterbox", "en-us")
