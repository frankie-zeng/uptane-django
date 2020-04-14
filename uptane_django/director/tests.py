from django.test import TestCase 
from django.conf import settings
import tuf.repository_tool as rt
import os
# Create your tests here.
class InventoryDBTests(TestCase):
    
    
    def test(self):
        
        
        vin = 'democar'
        settings.DIRECTOR.add_new_vehicle(vin)
        primary_serial = 'INFOdemocar'
        secondary_serial = 'TCUdemocar'

        primary_pub = rt.import_ed25519_publickey_from_file(os.path.join(settings.KEY_PATH, 'primary.pub'))
        secondary_pub = rt.import_ed25519_publickey_from_file(os.path.join(settings.KEY_PATH, 'secondary.pub'))


        settings.DIRECTOR.register_ecu_serial(primary_serial,primary_pub,vin,True)
        settings.DIRECTOR.register_ecu_serial(secondary_serial,secondary_pub,vin,False)

  
        manifest_json = {
        "signatures": [{
            "keyid": "9a406d99e362e7c93e7acfe1e4d6585221315be817f350c026bbee84ada260da",
            "method": "ed25519",
            "sig": "335272f77357dc0e9f1b74d72eb500e4ff0f443f824b83405e2b21264778d1610e0a5f2663b90eda8ab05a28b5b64fc15514020985d8a93576fe33b287e1380f"}],
        "signed": {
            "primary_ecu_serial": "INFOdemocar",
            "vin": "democar",
            "ecu_version_manifests": {
            "TCUdemocar": [{
            "signatures": [{
                "keyid": "49309f114b857e4b29bfbff1c1c75df59f154fbc45539b2eb30c8a867843b2cb",
                "method": "ed25519",
                "sig": "fd04c1edb0ddf1089f0d3fc1cd460af584e548b230d9c290deabfaf29ce5636b6b897eaa97feb64147ac2214c176bbb1d0fa8bb9c623011a0e48d258eb3f9108"}],
            "signed": {
                "attacks_detected": "",
                "ecu_serial": "TCUdemocar",
                "previous_timeserver_time": "2017-05-18T16:37:46Z",
                "timeserver_time": "2017-05-18T16:37:48Z",
                "installed_image": {
                "filepath": "/secondary_firmware.txt",
                "fileinfo": {
                "length": 37,
                "hashes": {
                "sha256": "6b9f987226610bfed08b824c93bf8b2f59521fce9a2adef80c495f363c1c9c44",
                "sha512": "706c283972c5ae69864b199e1cdd9b4b8babc14f5a454d0fd4d3b35396a04ca0b40af731671b74020a738b5108a78deb032332c36d6ae9f31fae2f8a70f7e1ce"}}}}}]}}}

        settings.DIRECTOR.register_vehicle_manifest('democar', 'INFOdemocar', manifest_json)
        settings.DIRECTOR.register_vehicle_manifest('democar', 'TCUdemocar', manifest_json)