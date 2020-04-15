from django.db import models
# Create your models here.
from django.db import models
from django.conf import settings
import shutil # For copying directory trees
import os



class ImageTarget(models.Model):
    name = models.CharField(max_length=255,primary_key=True)
    file = models.FileField()
    def __str__(self):
        return self.name+':'+self.file.name
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the "real" save() method.
        settings.REPO.targets.add_target(os.path.join(settings.MEDIA_ROOT,self.file.name))
        settings.REPO.mark_dirty(['timestamp', 'snapshot'])
        settings.REPO.write() # will be writeall() in most recent TUF branch

        # Move staged metadata (from the write above) to live metadata directory.

        if os.path.exists(os.path.join(settings.IMAGE_REPO, 'metadata')):
            shutil.rmtree(os.path.join(settings.IMAGE_REPO, 'metadata'))

        shutil.copytree(
            os.path.join(settings.IMAGE_REPO, 'metadata.staged'),
            os.path.join(settings.IMAGE_REPO, 'metadata'))