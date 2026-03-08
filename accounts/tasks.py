import requests
from library.models import Song
from .models import SpotifyToken
from .views import get_valid_token
from django.contrib.auth.models import User


def sync_user_library(user_id):
    user = User.objects.get(id=user_id)
    access_token = get_valid_token(user)
    headers = {"Authorization": f"Bearer {access_token}"}

    url = "https://api.spotify.com/v1/me/tracks?limit=50"

    while url:
        response = requests.get(url, headers=headers).json()

        artist_ids = []
        for item in response["items"]:
            artist_ids.append(item["track"]["artists"][0]["id"])

        artist_genres = {}
        if artist_ids:
            ids_str = ",".join(artist_ids[:50])
            artists_response = requests.get(
                f"https://api.spotify.com/v1/artists?ids={ids_str}",
                headers=headers
            ).json()
            for artist in artists_response["artists"]:
                genre = artist["genres"][0] if artist["genres"] else ""
                artist_genres[artist["id"]] = genre

        for item in response["items"]:
            track = item["track"]
            primary_artist = track["artists"][0]

            Song.objects.update_or_create(
                spotify_id=track["id"],
                defaults={
                    "user": user,
                    "title": track["name"],
                    "artist": primary_artist["name"],
                    "all_artists": [a["name"] for a in track["artists"]],
                    "album": track["album"]["name"],
                    "album_art_url": track["album"]["images"][0]["url"] if track["album"]["images"] else "",
                    "release_year": int(track["album"]["release_date"][:4]),
                    "date_added": item["added_at"],
                    "popularity": track["popularity"],
                    "genre": artist_genres.get(primary_artist["id"], ""),
                }
            )

        url = response.get("next")



