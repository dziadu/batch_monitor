from django.db import models

# Create your models here.
class BatchHostSettings(models.Model):
	name = models.CharField(max_length=200)
	host = models.CharField(max_length=200)
	user = models.CharField(max_length=200)
	port = models.IntegerField(default=22)
	sshpub = models.TextField(blank=True)
	fs_engine = models.CharField(max_length=100, blank=True)
	farm_engine = models.CharField(max_length=100, blank=True)