from django.contrib import admin
from .models import Ecu,Vehicle,Target
# Register your models here.
admin.site.register(Ecu)
admin.site.register(Vehicle)
admin.site.register(Target)