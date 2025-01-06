from django.contrib import admin

# Register your models here.
from .models import Match, MatchQueue, Problem

admin.site.register(Match)
admin.site.register(MatchQueue)
admin.site.register(Problem)