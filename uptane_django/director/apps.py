from django.apps import AppConfig
from django.conf import settings

import tuf.repository_tool as rt
import os
class DirectorConfig(AppConfig):
    name = 'director'
    def ready(self):
        import director.director as director

        if not os.path.exists(settings.DIRECTOR_REPO):
            os.makedirs(settings.DIRECTOR_REPO)
        keys_pri = {}
        keys_pub = {}
        for role in ['root', 'timestamp', 'snapshot']:
            keys_pri[role] = rt.import_ed25519_privatekey_from_file(os.path.join(settings.KEY_PATH, 'director' + role),password='pw')
            keys_pub[role] = rt.import_ed25519_publickey_from_file(os.path.join(settings.KEY_PATH, 'director' + role + '.pub'))

        # Because the demo's Director targets key is not named correctly....
        # TODO: Remove this and add 'targets' back to the role list above when
        #       the key is correctly renamed.
        keys_pri['targets'] = rt.import_ed25519_privatekey_from_file(os.path.join(settings.KEY_PATH, 'director'),password='pw')
        keys_pub['targets'] = rt.import_ed25519_publickey_from_file(os.path.join(settings.KEY_PATH, 'director.pub'))
        
        settings.DIRECTOR=director.Director(settings.DIRECTOR_REPO,keys_pri['root'],keys_pub['root'],
                keys_pri['timestamp'],keys_pub['timestamp'],
                keys_pri['snapshot'],keys_pub['snapshot'],
                keys_pri['targets'],keys_pub['targets'])
    

