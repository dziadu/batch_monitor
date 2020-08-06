from django.contrib import admin

# Register your models here.
from batch_farm_monitor.models import BatchHostSettings

#from batch_farm_monitor import models as batch_farm_monitor_models
from django.db.models.base import ModelBase


#class ChoiceInLine(admin.TabularInline):
    #model = Choice
    #extra = 3


class BatchHostSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                  {'fields' : ['name', 'enable_remote', 'remote_source', 'local_source', 'enable_file', 'file_source', 'sshpub', 'fs_engine', 'farm_engine', 'partitions']}),
        #('Date information',    {'fields' : ['secret'], 'classes': ['collapse']}),
    ]
    #inlines = [ChoiceInLine]
    list_display = [ 'name', 'enable_remote', 'remote_source', 'local_source', 'enable_file', 'file_source', 'fs_engine', 'farm_engine', 'partitions' ]
    #list_filter = [ 'pub_date' ]
    #search_fields = ['question']

admin.site.register(BatchHostSettings, BatchHostSettingsAdmin)

#for name, var in batch_farm_monitor_models.__dict__.items():
    #if type(var) is ModelBase:
        #admin.site.register(var)
