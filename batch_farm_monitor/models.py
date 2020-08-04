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
    host = models.CharField(max_length=200)
    user = models.CharField(max_length=200)
    port = models.IntegerField(default=22)
    sshpub = models.TextField(blank=True)
    fs_engine = models.CharField(max_length=100, blank=True)
    farm_engine = models.CharField(max_length=10, blank=True, choices=FARM_ENGINE_CHOICES)
    partitions = models.CharField(max_length=100, blank=True)
