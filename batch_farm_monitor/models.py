from django.db import models
from django.utils.translation import gettext as _

# Create your models here.
class BatchHostSettings(models.Model):
    FE_SLURM = 'slurm'
    FE_QSUB = 'qsub'
    FARM_ENGINE_CHOICES = [
        (FE_SLURM, _('Slurm')),
        (FE_QSUB, _('QSub')),
    ]

    name = models.CharField(max_length=200)
    enable_remote = models.BooleanField(default=False)
    remote_source = models.CharField(max_length=200, blank=True)
    local_source = models.BooleanField(default=False)
    enable_file = models.BooleanField(default=False)
    file_source = models.CharField(max_length=200, blank=True)
    sshpub = models.TextField(blank=True)
    fs_engine = models.CharField(max_length=100, blank=True)
    farm_engine = models.CharField(max_length=10, blank=True, choices=FARM_ENGINE_CHOICES)
    partitions = models.CharField(max_length=100, blank=True)

    def __str__(self):
        label = self.name
        label += " at " + self.remote_source if len(self.remote_source) else \
            " at local machine" if self.local_source else \
            " in " + self.file_source if len(self.file_source) else ""
        label += "  Engine: " + self.farm_engine if self.farm_engine else ""
        label += "  FairShare: " + self.fs_engine if self.fs_engine else ""
        return label
