from django.apps import AppConfig
from django.conf import settings

import tuf.repository_tool as rt
import os
import shutil

class ImageConfig(AppConfig):
    name = 'image'
    def ready(self):
        settings.REPO=rt.create_new_repository(settings.IMAGE_REPO)

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
        
        settings.REPO.root.add_verification_key(keys_pub['root'])
        settings.REPO.timestamp.add_verification_key(keys_pub['timestamp'])
        settings.REPO.snapshot.add_verification_key(keys_pub['snapshot'])
        settings.REPO.targets.add_verification_key(keys_pub['targets'])
        settings.REPO.root.load_signing_key(keys_pri['root'])
        settings.REPO.timestamp.load_signing_key(keys_pri['timestamp'])
        settings.REPO.snapshot.load_signing_key(keys_pri['snapshot'])
        settings.REPO.targets.load_signing_key(keys_pri['targets'])

        settings.REPO.mark_dirty(['timestamp', 'snapshot'])
        settings.REPO.write() # will be writeall() in most recent TUF branch

        # Move staged metadata (from the write above) to live metadata directory.

        if os.path.exists(os.path.join(settings.IMAGE_REPO, 'metadata')):
            shutil.rmtree(os.path.join(settings.IMAGE_REPO, 'metadata'))

        shutil.copytree(
            os.path.join(settings.IMAGE_REPO, 'metadata.staged'),
            os.path.join(settings.IMAGE_REPO, 'metadata'))