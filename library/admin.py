from django.contrib import admin
from .models import Song


# Register your models here.

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "spotify_id",
        "title",
        "artist",
        "album",
        'album_art_url',
        'release_year',
        'popularity',
        'genre',
        "date_added"
    ]