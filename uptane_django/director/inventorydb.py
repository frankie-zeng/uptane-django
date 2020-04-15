import uptane  # Import before TUF modules; may change tuf.conf values.
import uptane.formats
import tuf
import sys
from .models import Ecu,Vehicle
import json

# Global dictionaries
vehicle_manifests = {}
ecu_manifests = {}



def get_ecu_public_key(ecu_serial):
    try:
        ecu = Ecu.objects.get(identifier=ecu_serial)
    except:
        raise uptane.UnknownECU('The given ECU Serial, ' + repr(ecu_serial) +
                                ' is not known. It must be registered.')
    #print(type(ecu.public_key))
    return json.loads(ecu.public_key)
    #return ecu.public_key


def register_ecu(is_primary, vin, ecu_serial, public_key):
    tuf.formats.BOOLEAN_SCHEMA.check_match(is_primary)
    uptane.formats.VIN_SCHEMA.check_match(vin)
    uptane.formats.ECU_SERIAL_SCHEMA.check_match(ecu_serial)
    tuf.formats.ANYKEY_SCHEMA.check_match(public_key)
    ecus = Ecu.objects.filter(vehicle_id=vin)
    for ecu in ecus:
        if is_primary and ecu.primary:
            raise uptane.Spoofing('The given VIN, ' + repr(vin) + ', is already '
                                  'associated with a Primary ECU.')
        if ecu.identifier == ecu_serial:
            raise uptane.Spoofing('The given ECU Serial, ' + repr(ecu_serial) +
                                  ', is already associated with a public key.')

    check_vin_registered(vin)

    newecu = Ecu(
        identifier=ecu_serial,
        public_key=json.dumps(public_key),
        primary=is_primary,
        vehicle_id=Vehicle.objects.get(identifier=vin)
    )
    newecu.save()

    # Create an entry in the ecu_manifests dictionary for future manifests from
    # the ECU.
    ecu_manifests[ecu_serial] = []

def get_all_registed_vin():
    return Vehicle.objects.all()

def register_vehicle(vin):
    vins = Vehicle.objects.filter(identifier=vin)
    if len(vins) == 0:
        newvin = Vehicle(
            identifier=vin,
        )
        newvin.save()
    else:
        raise uptane.Spoofing('The given VIN, ' + repr(vin) + ', is already '
                              'registered.')
    vehicle_manifests[vin] = []


def check_vin_registered(vin):
    try:
        Vehicle.objects.get(identifier=vin)
    except:
        raise uptane.UnknownVehicle('The given VIN, ' + repr(vin) + ', is not '
                                    'known.')


def check_ecu_registered(ecu_serial):
    try:
        Ecu.objects.get(identifier=ecu_serial)
    except:
        raise uptane.UnknownECU('The given ECU serial, ' + repr(ecu_serial) +
                                ', is not known.')


def get_vehicle_manifests(vin):
    check_vin_registered(vin)
    return vehicle_manifests[vin]


def get_last_vehicle_manifest(vin):
    check_vin_registered(vin)
    if not vehicle_manifests[vin]:
        return None
    else:
        return vehicle_manifests[vin][-1]


def get_ecu_manifests(ecu_serial):
    check_ecu_registered(ecu_serial)
    return ecu_manifests[ecu_serial]


def get_last_ecu_manifest(ecu_serial):
    check_ecu_registered(ecu_serial)
    if not ecu_manifests[ecu_serial]:
        return None
    else:
        return ecu_manifests[ecu_serial][-1]


def save_vehicle_manifest(vin, signed_vehicle_manifest):
    """
    Given a manifest of form
    uptane.formats.SIGNABLE_VEHICLE_VERSION_MANIFEST_SCHEMA, save it in an index
    by vin, and save the individual ecu attestations in an index by ecu serial.
    """
    check_vin_registered(vin)  # check arg format and registration

    uptane.formats.SIGNABLE_VEHICLE_VERSION_MANIFEST_SCHEMA.check_match(
        signed_vehicle_manifest)

    vehicle_manifests[vin].append(signed_vehicle_manifest)

    # Not doing it this way because the Director is going to pass through a
    # correctly-signed vehicle manifest even if some of the ECU Manifests within
    # it are *not* correctly signed. The Director will instead issue a
    # save_ecu_manifest call for each validly-signed ECU Manifest.
    # # Save all the contained ECU manifests.
    # all_contained_ecu_manifests = signed_vehicle_manifest['signed'][
    #     'ecu_version_manifests']

    # for ecu_serial in all_contained_ecu_manifests:
    #   for signed_ecu_manifest in all_contained_ecu_manifests[ecu_serial]:
    #     save_ecu_manifest(ecu_serial, signed_ecu_manifest)


def get_all_ecu_manifests_from_vehicle(vin):
    """
    Returns a dictionary of lists of manifests, indexed by the ECU Serial of each
    ECU associated with the given VIN. (This is the same format as the
    ecu_manifests global, but only includes those ECUs associated with the
    vehicle.)

    e.g.
      {'ecuserial1': [<ecumanifest>, <ecumanifest>],
       'ecuserial9': []}
    """

    check_vin_registered(vin)  # check arg format and registration

    ecus_in_vehicle = ecus_by_vin[vin]

    return {serial: ecu_manifests[serial] for serial in ecus_in_vehicle}


def save_ecu_manifest(vin, ecu_serial, signed_ecu_manifest):

    check_ecu_registered(ecu_serial)  # check format and registration

    uptane.formats.SIGNABLE_ECU_VERSION_MANIFEST_SCHEMA.check_match(
        signed_ecu_manifest)

    ecu_manifests[ecu_serial].append(signed_ecu_manifest)
