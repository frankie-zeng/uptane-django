from django.db import models
from django.conf import settings
from image.models import ImageTarget
import shutil # For copying directory trees
import os
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Vehicle(models.Model):
    identifier = models.CharField(max_length=17, primary_key=True, unique=True)
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        print(self.identifier)
        settings.DIRECTOR.create_director_repo_for_vehicle(self.identifier)



class Ecu(models.Model):
    identifier = models.CharField(max_length=64, primary_key=True, unique=True)
    public_key = models.TextField()
    primary = models.BooleanField()
    vehicle_id = models.ForeignKey('Vehicle', models.PROTECT)

class Target(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.ForeignKey(ImageTarget,models.PROTECT)
    ecu = models.ForeignKey('Ecu', models.PROTECT)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        vin=self.ecu.vehicle_id.identifier
        ecu_serial=self.ecu.identifier
        repo = settings.DIRECTOR.vehicle_repositories[vin]
        repo_dir = repo._repository_directory
        destination_filepath = os.path.join(repo_dir, 'targets', self.image.file.name)
        # TODO: This should probably place the file into a common targets directory
        # that is then softlinked to all repositories.
        shutil.copy(os.path.join(settings.MEDIA_ROOT,self.image.file.name), destination_filepath)
        settings.DIRECTOR.add_target_for_ecu(vin,ecu_serial,destination_filepath)

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

@receiver(post_delete, sender=Target)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    vin=instance.ecu.vehicle_id.identifier
    repo = settings.DIRECTOR.vehicle_repositories[vin]
    repo_dir = repo._repository_directory
    destination_filepath = os.path.join(repo_dir, 'targets', instance.image.file.name)
    try:
        settings.DIRECTOR.delete_target_for_vechile(vin,destination_filepath)
        os.remove(destination_filepath)
    except:
        pass
    
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