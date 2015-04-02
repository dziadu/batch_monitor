from django.contrib import admin

# Register your models here.
from batch_monitor.models import BatchHostSettings

#from batch_monitor import models as batch_monitor_models
from django.db.models.base import ModelBase


#class ChoiceInLine(admin.TabularInline):
    #model = Choice
    #extra = 3


class BatchHostSettingsAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,                  {'fields' : ['name', 'host', 'user', 'port', 'sshpub', 'fs_engine', 'farm_engine']}),
        #('Date information',    {'fields' : ['secret'], 'classes': ['collapse']}),
    ]
    #inlines = [ChoiceInLine]
    list_display = [ 'name', 'host', 'user', 'port', 'fs_engine', 'farm_engine' ]
    #list_filter = [ 'pub_date' ]
    #search_fields = ['question']

admin.site.register(BatchHostSettings, BatchHostSettingsAdmin)

#for name, var in batch_monitor_models.__dict__.items():
    #if type(var) is ModelBase:
        #admin.site.register(var)