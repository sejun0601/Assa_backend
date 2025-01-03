from django.contrib import admin

# Register your models here.
from .models import Video, VideoStatsHistory

admin.site.register(Video)
admin.site.register(VideoStatsHistory)