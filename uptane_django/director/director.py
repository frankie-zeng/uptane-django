import uptane # Import before TUF modules; may change tuf.conf values.
import uptane.formats
import uptane.common
import uptane.encoding.asn1_codec as asn1_codec
import tuf
import tuf.formats
import tuf.repository_tool as rt
#import uptane.ber_encoder as ber_encoder
from uptane import GREEN, RED, YELLOW, ENDCOLORS
import director.inventorydb as inventory
import os
import hashlib
import json
import shutil

from uptane.encoding.asn1_codec import DATATYPE_TIME_ATTESTATION
from uptane.encoding.asn1_codec import DATATYPE_ECU_MANIFEST
from uptane.encoding.asn1_codec import DATATYPE_VEHICLE_MANIFEST

log = uptane.logging.getLogger('director')
log.addHandler(uptane.file_handler)
log.addHandler(uptane.console_handler)
log.setLevel(uptane.logging.DEBUG)



class Director:
  """
  See file's docstring.

  Fields:

    key_dirroot_pri
      Private signing key for the root role in the Director's repositories

    key_dirtime_pri
      Private signing key for the timestamp role in the Director's repositories

    key_dirsnap_pri
      Private signing key for the snapshot role in the Director's repositories

    key_dirtarg_pri
      Private signing key for the targets role in the Director's repositories

    vehicle_repositories
      A dictionary of tuf.repository_tool.Repository objects, indexed by VIN.
      Each holds the Director metadata geared toward that particular vehicle.

    director_repos_dir
      The root directory in which the repositories for each vehicle reside.

  """


  def __init__(self,
    director_repos_dir,
    key_root_pri,
    key_root_pub,
    key_timestamp_pri,
    key_timestamp_pub,
    key_snapshot_pri,
    key_snapshot_pub,
    key_targets_pri,
    key_targets_pub):

    """
    """

    tuf.formats.RELPATH_SCHEMA.check_match(director_repos_dir)

    for key in [
        key_root_pri, key_root_pub, key_timestamp_pri, key_timestamp_pub,
        key_snapshot_pri, key_snapshot_pub, key_targets_pri, key_targets_pub]:
      tuf.formats.ANYKEY_SCHEMA.check_match(key)

    self.director_repos_dir = director_repos_dir

    self.key_dirroot_pri = key_root_pri
    self.key_dirroot_pub = key_root_pub
    self.key_dirtime_pri = key_timestamp_pri
    self.key_dirtime_pub = key_timestamp_pub
    self.key_dirsnap_pri = key_snapshot_pri
    self.key_dirsnap_pub = key_snapshot_pub
    self.key_dirtarg_pri = key_targets_pri
    self.key_dirtarg_pub = key_targets_pub

    self.vehicle_repositories = dict()

    try:
      vins=inventory.get_all_registed_vin()
    except:
      pass
      vins=[]
    for vin in vins:
      # inventory.load_manifests_dict(vin.identifier)
      self.create_director_repo_for_vehicle(vin.identifier)
      repo=self.vehicle_repositories[vin.identifier]
      repo_dir=repo._repository_directory
      targets_json=os.path.join(repo_dir,'metadata','targets.json')
      if os.path.exists(targets_json):
        f=open(targets_json)
        targets_meta=json.loads(f.read())
        f.close()
        targets=targets_meta['signed']['targets']
        for key in targets.keys():
          filepath=os.path.join(repo_dir,'targets',key[1:])
          ecu_serial=targets[key]['custom']['ecu_serial']
          if os.path.exists(filepath):
            self.add_target_for_ecu(vin.identifier,ecu_serial,filepath)
      self.write_to_live(vin.identifier)
   

  def write_to_live(self,vin):
    repo=self.vehicle_repositories[vin]
    repo_dir = repo._repository_directory

    repo.mark_dirty(['timestamp', 'snapshot'])
    repo.write() # will be writeall() in most recent TUF branch
    assert(os.path.exists(os.path.join(repo_dir, 'metadata.staged'))), \
        'Programming error: a repository write just occurred; why is ' + \
        'there no metadata.staged directory where it is expected?'

    # This shouldn't exist, but just in case something was interrupted,
    # warn and remove it.
    if os.path.exists(os.path.join(repo_dir, 'metadata.livetemp')):
        print(LOG_PREFIX + YELLOW + 'Warning: metadata.livetemp existed already. '
            'Some previous process was interrupted, or there is a programming '
            'error.' + ENDCOLORS)
        shutil.rmtree(os.path.join(repo_dir, 'metadata.livetemp'))

    # Copy the staged metadata to a temp directory we'll move into place
    # atomically in a moment.
    shutil.copytree(
        os.path.join(repo_dir, 'metadata.staged'),
        os.path.join(repo_dir, 'metadata.livetemp'))

    # Empty the existing (old) live metadata directory (relatively fast).
    if os.path.exists(os.path.join(repo_dir, 'metadata')):
        shutil.rmtree(os.path.join(repo_dir, 'metadata'))

    # Atomically move the new metadata into place.
    os.rename(
        os.path.join(repo_dir, 'metadata.livetemp'),
        os.path.join(repo_dir, 'metadata'))


  def register_ecu_serial(self, ecu_serial, ecu_key, vin, is_primary=False):
    """
    Set the expected public key for signed messages from the ECU with the given
    ECU Serial. If signed messages purportedly coming from the ECU with that
    ECU Serial are not signed by the given key, they will not be trusted.

    This also associates the ECU Serial with the given VIN, so that the
    Director will treat this ECU as part of that vehicle.

    Exceptions
      uptane.UnknownVehicle
        if the VIN is not known.

      uptane.Spoofing
        if the given ECU Serial already has a registered public key.
        (That is, this public method is not how you should replace the public
        key a given ECU uses.)

      uptane.FormatError or tuf.FormatError
        if the arguments do not fit the correct format.
    """
    uptane.formats.VIN_SCHEMA.check_match(vin)
    uptane.formats.ECU_SERIAL_SCHEMA.check_match(ecu_serial)
    tuf.formats.ANYKEY_SCHEMA.check_match(ecu_key)

    inventory.check_vin_registered(vin)

    # Register the public key and associate the ECU with the given VIN.
    inventory.register_ecu(
        is_primary, vin, ecu_serial, ecu_key)

    log.info(
        GREEN + 'Registered a new ECU, ' + repr(ecu_serial) + ' in '
        'vehicle ' + repr(vin) + ' with ECU public key: ' + repr(ecu_key) +
        ENDCOLORS)





  def validate_ecu_manifest(self, ecu_serial, signed_ecu_manifest):
    """
    Arguments:
      ecuid: uptane.formats.ECU_SERIAL_SCHEMA
      manifest: uptane.formats.SIGNABLE_ECU_VERSION_MANIFEST_SCHEMA
    """
    uptane.formats.ECU_SERIAL_SCHEMA.check_match(ecu_serial)
    uptane.formats.SIGNABLE_ECU_VERSION_MANIFEST_SCHEMA.check_match(
        signed_ecu_manifest)

    # If it doesn't match expectations, error out here.

    if ecu_serial != signed_ecu_manifest['signed']['ecu_serial']:
      raise uptane.Spoofing('Received a spoofed or mistaken manifest: supposed '
          'origin ECU (' + repr(ecu_serial) + ') is not the same as what is '
          'signed in the manifest itself (' +
          repr(signed_ecu_manifest['signed']['ecu_serial']) + ').')

    # if ecu_serial not in inventory.ecu_public_keys:
    #   log.info(
    #       'Validation failed on an ECU Manifest: ECU ' + repr(ecu_serial) +
    #       ' is not registered.')
    #   raise uptane.UnknownECU('The Director is not aware of the given ECU '
    #       'SERIAL (' + repr(ecu_serial) + '. Manifest rejected. If the ECU is '
    #       'new, Register the new ECU with its key in order to be able to '
    #       'submit its manifests.')

    ecu_public_key = inventory.get_ecu_public_key(ecu_serial)


    valid = uptane.common.verify_signature_over_metadata(
        ecu_public_key,
        signed_ecu_manifest['signatures'][0], # TODO: Fix single-signature assumption
        signed_ecu_manifest['signed'],
        DATATYPE_ECU_MANIFEST)

    if not valid:
      log.info(
          'Validation failed on an ECU Manifest: signature is not valid. '
          'It must be correctly signed by the expected key for that ECU.')
      raise tuf.BadSignatureError('Sender supplied an invalid signature. '
          'ECU Manifest is unacceptable. If you see this persistently, it is '
          'possible that the Primary is compromised or that there is a man in '
          'the middle attack or misconfiguration.')





  def register_vehicle_manifest(
      self, vin, primary_ecu_serial, signed_vehicle_manifest):
    """
    Saves the vehicle manifest in the InventoryDB, validating first the
    Primary's key on the full vehicle manifest, then each individual ECU
    Manifest's signature.

    If the Primary's signature over the whole Vehicle Manifest is invalid, then
    this raises an error (either tuf.BadSignatureError, uptane.Spoofing, or
    uptane.UnknownECU).

    Otherwise, if any of the individual ECU Manifests are invalid, those
    individual ECU Manifests are discarded, and others are processed. (No
    error is raised - only a warning.)

    Arguments:
      vin: vehicle's unique identifier, uptane.formats.VIN_SCHEMA
      primary_ecu_serial: Primary ECU's unique identifier,
                          uptane.formats.ECU_SERIAL_SCHEMA
      manifest: the vehicle manifest, as specified in the implementation
                specification and compliant with
                uptane.formats.SIGNABLE_VEHICLE_VERSION_MANIFEST_SCHEMA
                If, the metadata format is set to ASN.1/DER, then this will
                instead be compliant with uptane.formats.DER_DATA_SCHEMA,
                and will be decoded and converted back to be compliant with
                uptane.formats.SIGNABLE_VEHICLE_VERSION_MANIFEST_SCHEMA


    Exceptions:

        tuf.BadSignatureError
          if the Primary's signature on the vehicle manifest is invalid
          (An individual Secondary's signature on an ECU Version Manifests
          being invalid does not raise an exception, but instead results in
          a warning and that ECU Version Manifest alone being discarded.)

        uptane.Spoofing
          if the primary_ecu_serial argument does not match the ECU Serial
          for the Primary in the signed Vehicle Version Manifest.
          (As above, an ECU Version Manifest that is wrong in this respect is
          individually discarded with only a warning.)

        uptane.UnknownECU
          if the ECU Serial provided for the Primary is not known to this
          Director.
          (As above, an unknown Secondary ECU in an ECU Version Manifest is
          individually discarded with only a warning.)

        uptane.UnknownVehicle
          if the VIN provided is not known to this Director

    """
    uptane.formats.VIN_SCHEMA.check_match(vin)
    uptane.formats.ECU_SERIAL_SCHEMA.check_match(primary_ecu_serial)

    if tuf.conf.METADATA_FORMAT == 'der':
      # Check format and convert back to expected vehicle manifest format.
      uptane.formats.DER_DATA_SCHEMA.check_match(signed_vehicle_manifest)
      signed_vehicle_manifest = asn1_codec.convert_signed_der_to_dersigned_json(
          signed_vehicle_manifest, DATATYPE_VEHICLE_MANIFEST)

    uptane.formats.SIGNABLE_VEHICLE_VERSION_MANIFEST_SCHEMA.check_match(
        signed_vehicle_manifest)

    inventory.check_vin_registered(vin)
    # if vin not in inventory.ecus_by_vin:
    #   raise uptane.UnknownVehicle('Received a vehicle manifest purportedly '
    #       'from a vehicle with a VIN that is not known to this Director.')

    # Process Primary's signature on full manifest here.
    # If it doesn't match expectations, error out here.
    self.validate_primary_certification_in_vehicle_manifest(
        vin, primary_ecu_serial, signed_vehicle_manifest)

    # If the Primary's signature is valid, save the whole vehicle manifest to
    # the inventorydb.
    inventory.save_vehicle_manifest(vin, signed_vehicle_manifest)

    log.info(GREEN + ' Received a Vehicle Manifest from Primary ECU ' +
        repr(primary_ecu_serial) + ', with a valid signature from that ECU.' +
        ENDCOLORS)
    # TODO: Note that the above hasn't checked that the signature was from
    # a Primary, just from an ECU. Fix.


    # Validate signatures on and register all individual ECU manifests for each
    # ECU (may have multiple manifests per ECU).
    all_ecu_manifests = \
        signed_vehicle_manifest['signed']['ecu_version_manifests']

    for ecu_serial in all_ecu_manifests:
      ecu_manifests = all_ecu_manifests[ecu_serial]
      for manifest in ecu_manifests:
        try:
          # This calls validate_ecu_manifest, which can raise the errors
          # caught below.
          self.register_ecu_manifest(vin, ecu_serial, manifest)
        except uptane.Spoofing as e:
          log.warning(
              RED + 'Discarding a spoofed or malformed ECU Manifest. Error '
              ' from validating that ECU manifest follows:\n' + ENDCOLORS +
              repr(e))
        except uptane.UnknownECU as e:
          log.warning(
              RED + 'Discarding an ECU Manifest from unknown ECU. Error from '
              'validation attempt follows:\n' + ENDCOLORS + repr(e))
        except tuf.BadSignatureError as e:
          log.warning(
              RED + 'Rejecting an ECU Manifest whose signature is invalid, '
              'from within an otherwise valid Vehicle Manifest. Error from '
              'validation attempt follows:\n' + ENDCOLORS + repr(e))





  def validate_primary_certification_in_vehicle_manifest(
      self, vin, primary_ecu_serial, vehicle_manifest):
    """
    Check the Primary's signature on the Vehicle Manifest and any other data
    the Primary is certifying, without diving into the individual ECU Manifests
    in the Vehicle Manifest.

    Raises an exception if there is an issue with the Primary's signature.
    No return value.
    """
    # If args don't match expectations, error out here.
    log.info('Beginning validate_primary_certification_in_vehicle_manifest')
    uptane.formats.VIN_SCHEMA.check_match(vin)
    uptane.formats.ECU_SERIAL_SCHEMA.check_match(primary_ecu_serial)
    uptane.formats.SIGNABLE_VEHICLE_VERSION_MANIFEST_SCHEMA.check_match(
        vehicle_manifest)


    if primary_ecu_serial != vehicle_manifest['signed']['primary_ecu_serial']:
      raise uptane.Spoofing('Received a spoofed or mistaken vehicle manifest: '
          'the supposed origin Primary ECU (' + repr(primary_ecu_serial) + ') '
          'is not the same as what is signed in the vehicle manifest itself ' +
          '(' + repr(vehicle_manifest['signed']['primary_ecu_serial']) + ').')

    # # TODO: Consider mechanism for fetching keys from inventorydb itself,
    # # rather than always registering them after Director svc starts up.
    # if primary_ecu_serial not in inventory.ecu_public_keys:
    #   log.debug(
    #       'Rejecting a vehicle manifest from a Primary ECU whose '
    #       'key is not registered.')
    #   raise uptane.UnknownECU('The Director is not aware of the given Primary '
    #       'ECU Serial (' + repr(primary_ecu_serial) + '. Manifest rejected. If '
    #       'the ECU is new, Register the new ECU with its key in order to be '
    #       'able to submit its manifests.')

    ecu_public_key = inventory.get_ecu_public_key(primary_ecu_serial)

    # Here, we check to see if the key that signed the Vehicle Manifest is the
    # same key as ecu_public_key (the one the director expects), so that we can
    # generate a more informative error, allowing user/debugger to distinguish
    # between a bad signature ostensibly from the right key and a signature
    # from the wrong key.
    # TODO: Fix(?) assumption that one signature is used below.
    keyid_used_in_signature = vehicle_manifest['signatures'][0]['keyid']
    # Note, though, that there could be some edge cases here that the TUF code
    # might actually resolve: for example, if the keyid hash algorithm used
    # in the signature is not the same one as the one used in the key listing,
    # this check would provide a false failure. So we don't raise an error here,
    # and instead just log this difference and let the final arbiter of the
    # validity of the signature be the dedicated code in tuf.keys.
    if keyid_used_in_signature != ecu_public_key['keyid']:
      log.info(
          'Key used to sign Vehicle Manifest has a different keyid from that '
          'listed in the inventory DB. Expect signature validation to fail, '
          'unless the key is the same but the keyid differently hashed. '
          'Expected keyid: ' + repr(ecu_public_key['keyid']) + '; keyid used '
          'in signature: ' + repr(keyid_used_in_signature))


    if tuf.conf.METADATA_FORMAT == 'der':
      # To check the signature, we have to make sure to encode the data as it
      # was when the signature was made. If we're using ASN.1/DER as the
      # data format/encoding, then we convert the 'signed' portion of the data
      # back to ASN.1/DER to check it.
      # Further, since for ASN.1/DER, a SHA256 hash is taken of the data and
      # *that* is what is signed, we perform that hashing as well and retrieve
      # the raw binary digest.
      data_to_check = asn1_codec.convert_signed_metadata_to_der(
          vehicle_manifest, DATATYPE_VEHICLE_MANIFEST, only_signed=True)
      data_to_check = hashlib.sha256(data_to_check).digest()

    else:
      data_to_check = vehicle_manifest['signed']


    valid = uptane.common.verify_signature_over_metadata(
        ecu_public_key,
        vehicle_manifest['signatures'][0], # TODO: Fix assumptions.
        vehicle_manifest['signed'],
        DATATYPE_VEHICLE_MANIFEST)

    if not valid:
      log.debug(
          'Rejecting a vehicle manifest because the Primary signature on it is '
          'not valid. It must be correctly signed by the expected Primary ECU '
          'key.')
      raise tuf.BadSignatureError('Sender supplied an invalid signature. '
          'Vehicle Manifest is questionable; discarding. If you see this '
          'persistently, it is possible that there is a man in the middle '
          'attack or misconfiguration.')





  def register_ecu_manifest(self, vin, ecu_serial, signed_ecu_manifest):
    """
    """
    # Error out if the signature isn't valid and from the expected party.
    # Also checks argument format.
    self.validate_ecu_manifest(ecu_serial, signed_ecu_manifest)

    # Otherwise, we save it:
    inventory.save_ecu_manifest(vin, ecu_serial, signed_ecu_manifest)

    log.debug('Stored a valid ECU manifest from ECU ' + repr(ecu_serial))

    # Alert if there's been a detected attack.
    if signed_ecu_manifest['signed']['attacks_detected']:
      log.warning(
          YELLOW + 'Attacks have been reported by the Secondary ECU ' +
          repr(ecu_serial) + ':\n' +
          signed_ecu_manifest['signed']['attacks_detected'] + ENDCOLORS)





  def add_new_vehicle(self, vin):
    """
    For adding vehicles whose VINs were not provided when this object was
    initialized.

    Note that individual ECUs should also be registered, providing their
    public keys.

    """
    # TODO: The VIN string is manipulated for create_director_repo_for_vehicle,
    # but the string is not manipulated for this addition to ecus_by_vin.
    # Treatment has to be made consistent. (In particular, things like slashes
    # are pruned - or an error is raised when they are detected.)
    inventory.register_vehicle(vin)

    self.create_director_repo_for_vehicle(vin)





  def create_director_repo_for_vehicle(self, vin):
    """
    Creates a separate repository object for a given vehicle identifier.
    Each uses the same keys.
    Ideally, each would use the same root.json file, but that will have to
    wait until TUF Augmentation Proposal 5 (when the hash of root.json ceases
    to be included in snapshot.json).

    The name of each repository is the VIN string.

    If the repository already exists, it is overwritten.

    Usage:

      d = uptane.services.director.Director(...)
      d.create_director_repo_for_vehicle(vin)
      d.add_target_for_ecu(vin, ecu, target_filepath)

    These repository objects can be manipulated as described in TUF
    documentation; for example, to produce metadata files afterwards for that
    vehicle:
      d.vehicle_repositories[vin].write()


    # TODO: This may be outside of the scope of the reference implementation,
    # and best to put in the demo code. It's not clear what should live in the
    # reference implementation itself for this....

    """

    uptane.formats.VIN_SCHEMA.check_match(vin)

    # Repository Tool expects to use the current directory.
    # Figure out if this is impactful and needs to be changed.
    last_dir=os.getcwd()
    os.chdir(self.director_repos_dir) # TODO: Is messing with cwd a bad idea?

    # Generates absolute path for a subdirectory with name equal to vin,
    # in the current directory, making (relatively) sure that there isn't
    # anything suspect like "../" in the VIN.
    # Then I strip the common prefix back off the absolute path to get a
    # relative path and keep the guarantees.
    # TODO: Clumsy and hacky; fix.
    vin = uptane.common.scrub_filename(vin, self.director_repos_dir)
    vin = os.path.relpath(vin, self.director_repos_dir)

    self.vehicle_repositories[vin] = this_repo = rt.create_new_repository(
        vin, repository_name=vin)


    this_repo.root.add_verification_key(self.key_dirroot_pub)
    this_repo.timestamp.add_verification_key(self.key_dirtime_pub)
    this_repo.snapshot.add_verification_key(self.key_dirsnap_pub)
    this_repo.targets.add_verification_key(self.key_dirtarg_pub)
    this_repo.root.load_signing_key(self.key_dirroot_pri)
    this_repo.timestamp.load_signing_key(self.key_dirtime_pri)
    this_repo.snapshot.load_signing_key(self.key_dirsnap_pri)
    this_repo.targets.load_signing_key(self.key_dirtarg_pri)

    os.chdir(last_dir)


  def delete_target_for_vechile(self,vin,target_filepath):
    uptane.formats.VIN_SCHEMA.check_match(vin)
    tuf.formats.RELPATH_SCHEMA.check_match(target_filepath)

    if vin not in self.vehicle_repositories:
      raise uptane.UnknownVehicle('The VIN provided, ' + repr(vin) + ' is not '
          'that of a vehicle known to this Director.')

    # With the below off, we will save targets for ECUs we didn't previously
    # know exist.
    # elif ecu_serial not in inventory.ecu_public_keys:
    #   raise uptane.UnknownECU('The ECU Serial provided, ' + repr(ecu_serial) +
    #       ' is not that of an ECU known to this Director.')

    self.vehicle_repositories[vin].targets.remove_target(
        target_filepath)

  def add_target_for_ecu(self, vin, ecu_serial, target_filepath):
    """
    Add a target to the repository for a vehicle, marked as being for a
    specific ECU.

    The target file at the provided path will be analyzed, and its hashes
    and file length will be saved in target metadata in memory, which will then
    be signed with the appropriate Director keys and written to disk when the
    "write" method is called on the vehicle repository.
    """
    uptane.formats.VIN_SCHEMA.check_match(vin)
    uptane.formats.ECU_SERIAL_SCHEMA.check_match(ecu_serial)
    tuf.formats.RELPATH_SCHEMA.check_match(target_filepath)

    if vin not in self.vehicle_repositories:
      raise uptane.UnknownVehicle('The VIN provided, ' + repr(vin) + ' is not '
          'that of a vehicle known to this Director.')

    # With the below off, we will save targets for ECUs we didn't previously
    # know exist.
    # elif ecu_serial not in inventory.ecu_public_keys:
    #   raise uptane.UnknownECU('The ECU Serial provided, ' + repr(ecu_serial) +
    #       ' is not that of an ECU known to this Director.')

    self.vehicle_repositories[vin].targets.add_target(
        target_filepath, custom={'ecu_serial': ecu_serial})
