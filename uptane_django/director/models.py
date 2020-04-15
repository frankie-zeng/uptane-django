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
        settings.DIRECTOR.create_director_repo_for_vehicle(self.identifier)
        settings.DIRECTOR.write_to_live(self.identifier)
    def __str__(self):
        return self.identifier



class Ecu(models.Model):
    identifier = models.CharField(max_length=64, primary_key=True, unique=True)
    public_key = models.TextField()
    primary = models.BooleanField()
    vehicle_id = models.ForeignKey('Vehicle', models.PROTECT)
    def __str__(self):
        return self.vehicle_id.identifier+':'+self.identifier

class Target(models.Model):
    id = models.AutoField(primary_key=True)
    image = models.ForeignKey(ImageTarget,models.PROTECT)
    ecu = models.ForeignKey('Ecu', models.PROTECT)
    def __str__(self):
        return self.ecu.vehicle_id.identifier+':'+self.ecu.identifier+'('+self.image.name+':'+self.image.file.name+')'
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
        settings.DIRECTOR.write_to_live(vin)
        

@receiver(post_delete, sender=Target)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    vin=instance.ecu.vehicle_id.identifier
    repo = settings.DIRECTOR.vehicle_repositories[vin]
    repo_dir = repo._repository_directory
    destination_filepath = os.path.join(repo_dir, 'targets', instance.image.file.name)
    settings.DIRECTOR.delete_target_for_vechile(vin,destination_filepath)
    os.remove(destination_filepath)
    
   
    
    settings.DIRECTOR.write_to_live(vin)
    