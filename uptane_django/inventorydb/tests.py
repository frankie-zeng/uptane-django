from django.test import TestCase
from .views import *
import sys
# Create your tests here.

class InventoryDBTests(TestCase):
    def test(self):
        print(register_vehicle("312312"))
        print(check_vin_registered("312312"))
        print(register_ecu(True,'312312','3123123','312312--rsa','31231'))
        print(get_ecu_public_key("3123123"))
        print(check_ecu_registered('312312311'))
   
        
        
            