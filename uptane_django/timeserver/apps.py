from django.apps import AppConfig
from django.conf import settings
import uptane.services.timeserver as timeserver
import tuf.repository_tool as rt
import os
class TimeserverConfig(AppConfig):
    name = 'timeserver'
    def ready(self):
        key=rt.import_rsa_privatekey_from_file(os.path.join(settings.KEY_PATH, 'timeserver'), password='pw')
        timeserver.set_timeserver_key(key)