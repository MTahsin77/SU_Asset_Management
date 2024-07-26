from django.contrib import admin
from .models import Asset, User, Allocation

admin.site.register(Asset)
admin.site.register(User)
admin.site.register(Allocation)