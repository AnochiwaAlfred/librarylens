from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Song(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Identity
    spotify_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)

    # Artist
    artist = models.CharField(max_length=255)  # primary artist (display)
    all_artists = models.JSONField(default=list)  # ["Frank Ocean", "André 3000"]

    # Album
    album = models.CharField(max_length=255)
    album_art_url = models.URLField(blank=True)  # cover image

    # Time
    release_year = models.IntegerField(null=True, blank=True)
    date_added = models.DateTimeField(null=True)  # when user liked it on Spotify

    # Stats
    popularity = models.IntegerField(default=0)  # 0–100, Spotify's score

    # Genre
    genre = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-date_added']



class LibrarySync(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=[
            ("idle", "Idle"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="idle"
    )

    progress = models.IntegerField(default=0)
    total = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)