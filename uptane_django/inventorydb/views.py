from django.shortcuts import render
from .models import Ecu, Vehicle
import uptane  # Import before TUF modules; may change tuf.conf values.
import uptane.formats
import tuf
import sys
# Create your views here.


def get_ecu_public_key(ecu_serial):
    try:
        ecu = Ecu.objects.get(identifier=ecu_serial)
    except :
        return None
    else:
        return ecu.public_key
def register_ecu(is_primary, vin, ecu_serial, public_key, cryptography_method):
    ecus = Ecu.objects.filter(identifier=ecu_serial)
    if len(ecus) == 0 :
        try:
            newecu=Ecu(
                identifier=ecu_serial,
                public_key=public_key,
                cryptography_method=cryptography_method,
                primary=is_primary,
                vehicle_id=Vehicle.objects.get(identifier=vin)
            )
            newecu.save()
        except Exception as e:
            return {
                "err":-1,
                "msg":str(e)
            }
    
    return {
        "err":0,
        "msg":"ok"
    }
    
def register_vehicle(vin):
    vins = Vehicle.objects.filter(identifier=vin)
    if len(vins) == 0 :
        try:
            newvin=Vehicle(
                identifier=vin,
            )
            newvin.save()
        except Exception as e:
            return {
                "err":-1,
                "msg":str(e)
            }
    
    return {
        "err":0,
        "msg":'ok'
    }
def check_vin_registered(vin):
    try:
        Vehicle.objects.get(identifier=vin)
    except :
        return False
    else:
        return True

def check_ecu_registered(ecu_serial):
    try:
        Ecu.objects.get(identifier=ecu_serial)
    except :
        return False
    else:
        return True  
