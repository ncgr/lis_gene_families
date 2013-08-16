from django.contrib import admin
from chado.models import Organism, Db

# regist models with the admin site
admin.site.register(Organism)
