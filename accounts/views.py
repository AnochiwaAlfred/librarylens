import base64
import csv
import json
import requests
import urllib.parse

from datetime import timedelta
from collections import defaultdict

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth import logout as django_logout
from django.core.paginator import Paginator
from django.db.models import Count, Avg
from django.db.models import Max
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from library.models import Song
from .models import SpotifyToken






def spotify_login(request):
    params = {
        "client_id": settings.SPOTIFY_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        "scope": settings.SPOTIFY_SCOPE,
        "show_dialog": True # Optional: Forces the "Accept" screen
    }
    # REAL Spotify Auth URL
    url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)
    return redirect(url)





def spotify_callback(request):
    code = request.GET.get("code")

    print("Coded")
    # Step 1 — exchange code for tokens
    credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.SPOTIFY_REDIRECT_URI,
        }
    )

    token_data = response.json()
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    expires_at = timezone.now() + timedelta(seconds=token_data["expires_in"])

    # Step 2 — get the user's Spotify profile
    print("Profile")
    profile = requests.get(
        "https://api.spotify.com/v1/me",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    spotify_username = profile["id"]

    # Step 3 — get or create a Django user
    user, _ = User.objects.get_or_create(username=spotify_username)
    login(request, user)

    # Step 4 — save the token
    SpotifyToken.objects.update_or_create(
        user=user,
        defaults={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
        }
    )

    return redirect("home")


def login_page(request):
    # If already logged in, skip the login page
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'accounts/login.html')


def spotify_logout(request):
    django_logout(request)
    return redirect('login_page')







@login_required(login_url='/login/')
def index(request):
    songs = Song.objects.filter(user=request.user)

    # ── Stat cards ──
    total           = songs.count()
    unique_artists  = songs.values('artist').distinct().count()
    unique_genres   = songs.exclude(genre='').values('genre').distinct().count()
    avg_year        = songs.aggregate(a=Avg('release_year'))['a']
    avg_year        = round(avg_year) if avg_year else '—'

    # ── Top artists ──
    top_artists = (
        songs.values('artist')
             .annotate(count=Count('artist'))
             .order_by('-count')[:5]
    )

    # ── Top genres ──
    top_genres = (
        songs.exclude(genre='')
             .values('genre')
             .annotate(count=Count('genre'))
             .order_by('-count')[:5]
    )
    top_genre_name = top_genres[0]['genre'].title() if top_genres else '—'
    genre_max      = top_genres[0]['count'] if top_genres else 1


    # Find the latest year in the database
    latest_year = songs.aggregate(Max('release_year'))['release_year__max'] or 2026

    # Filter for the last 10 years only
    songs_per_year = (
        songs.filter(release_year__gte=latest_year - 9)
        .values('release_year')
        .annotate(count=Count('id'))
        .order_by('release_year')
    )

    # We use a default of 1 to avoid DivisionByZero if the list is empty
    year_max = max([y['count'] for y in songs_per_year]) if songs_per_year else 1

    songs_per_year = [
        {
            'year': y['release_year'],
            'count': y['count'],
            'bar_h': round((y['count'] / year_max) * 140),
            'bar_y': 160 - round((y['count'] / year_max) * 140),
            'x': i * 70 + 10,
        }
        for i, y in enumerate(songs_per_year)
    ]


    # ── Newest / Oldest liked ──
    newest = songs.order_by('-date_added').first()
    oldest = songs.order_by('date_added').first()
    # In view, after newest/oldest:
    lifespan = newest.date_added.year - oldest.date_added.year if newest and oldest else 0
    # lifespan as a % of a 10-year scale, capped at 100
    lifespan_pct = min(round((lifespan / 10) * 100), 100) if lifespan else 50

    # ── Dashboard artists (with % bar width) ──
    artist_max = top_artists[0]['count'] if top_artists else 1
    top_artists_with_pct = [
        {**a, 'pct': round((a['count'] / artist_max) * 100)}
        for a in top_artists
    ]

    # ── Genre pills (top 6) ──
    genre_tags = [g['genre'].title() for g in top_genres[:6]]

    # ── Explorer: all songs + filters ──
    query   = request.GET.get('q', '')
    year    = request.GET.get('year', '')
    genre   = request.GET.get('genre', '')
    sort    = request.GET.get('sort', 'date_added')

    sort_map = {
        'date_added':   '-date_added',
        'popularity':   '-popularity',
        'release_year': '-release_year',
    }

    explorer_songs = songs
    if query:
        explorer_songs = explorer_songs.filter(
            title__icontains=query
        ) | explorer_songs.filter(
            artist__icontains=query
        ) | explorer_songs.filter(
            album__icontains=query
        )
    if year:
        explorer_songs = explorer_songs.filter(release_year=year)
    if genre:
        explorer_songs = explorer_songs.filter(genre__icontains=genre)

    explorer_songs = explorer_songs.order_by(sort_map.get(sort, '-date_added'))

    # Pagination
    paginator   = Paginator(explorer_songs, 10)
    page_number = request.GET.get('page', 1)
    page_obj    = paginator.get_page(page_number)

    # Year + genre options for dropdowns
    year_options  = songs.values_list('release_year', flat=True).distinct().order_by('-release_year')
    genre_options = songs.exclude(genre='').values_list('genre', flat=True).distinct().order_by('genre')

    context = {
        # Stats
        'total':          total,
        'unique_artists': unique_artists,
        'unique_genres':  unique_genres,
        'avg_year':       avg_year,
        # Dashboard
        'top_artists':    top_artists_with_pct,
        'top_genres':     top_genres,
        'top_genre_name': top_genre_name,
        'genre_max':      genre_max,
        'genre_tags':     genre_tags,
        'songs_per_year': list(songs_per_year),
        'newest':         newest,
        'oldest':         oldest,
        # Explorer
        'page_obj':       page_obj,
        'paginator':      paginator,
        'year_options':   year_options,
        'genre_options':  genre_options,
        'current_q':      query,
        'current_year':   year,
        'current_genre':  genre,
        'current_sort':   sort,
        'username':       request.user.username,
        'lifespan': lifespan,
        'lifespan_pct':    lifespan_pct,

    }

    return render(request, 'accounts/index.html', context=context)






@login_required(login_url='/login/')
def export_csv(request):
    songs = Song.objects.filter(user=request.user).order_by('-date_added')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="soundvault_liked_songs.csv"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Artist', 'Album', 'Release Year', 'Genre', 'Popularity', 'Date Added', 'Spotify ID'])

    for song in songs:
        writer.writerow([
            song.title,
            song.artist,
            song.album,
            song.release_year,
            song.genre,
            song.popularity,
            song.date_added.strftime('%Y-%m-%d'),
            song.spotify_id,
        ])

    return response


@login_required(login_url='/login/')
def export_json(request):
    songs = Song.objects.filter(user=request.user).order_by('-date_added')

    data = [
        {
            'title':        song.title,
            'artist':       song.artist,
            'all_artists':  song.all_artists,
            'album':        song.album,
            'release_year': song.release_year,
            'genre':        song.genre,
            'popularity':   song.popularity,
            'date_added':   song.date_added.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'album_art':    song.album_art_url,
            'spotify_id':   song.spotify_id,
        }
        for song in songs
    ]

    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = 'attachment; filename="soundvault_liked_songs.json"'
    return response


@login_required(login_url='/login/')
def export_txt(request):
    songs = Song.objects.filter(user=request.user).order_by('-date_added')

    lines = [
        f"Soundvault Export — {request.user.username}'s Library",
        f"Generated: {songs.first().date_added.strftime('%B %Y') if songs else '—'} · {songs.count()} songs",
        "─" * 40,
        "",
    ]

    for song in songs:
        lines.append(f"{song.artist} — {song.title}  ({song.release_year})")

    content = "\n".join(lines)

    response = HttpResponse(content, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="soundvault_liked_songs.txt"'
    return response


@login_required(login_url='/login/')
def export_md(request):
    songs = Song.objects.filter(user=request.user).order_by('artist', '-date_added')

    # Group songs by artist
    grouped = defaultdict(list)
    for song in songs:
        grouped[song.artist].append(song)

    # Sort artists by number of songs (most first)
    sorted_artists = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)

    lines = [
        f"# {request.user.username}'s Liked Songs",
        f"_Exported via Soundvault · {songs.count()} songs_",
        "",
    ]

    for artist, artist_songs in sorted_artists:
        lines.append(f"## {artist} ({len(artist_songs)} songs)")
        for song in artist_songs:
            lines.append(f"- {song.title} _({song.album}, {song.release_year})_")
        lines.append("")  # blank line between artists

    content = "\n".join(lines)

    response = HttpResponse(content, content_type='text/markdown')
    response['Content-Disposition'] = 'attachment; filename="soundvault_liked_songs.md"'
    return response



def get_valid_token(user):
    """Returns a valid access token, refreshing it if expired."""
    token = SpotifyToken.objects.get(user=user)

    if token.expires_at <= timezone.now():
        # Token expired — refresh it
        credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
        encoded = base64.b64encode(credentials.encode()).decode()

        response = requests.post(
            "https://accounts.spotify.com/api/token",
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "refresh_token",
                "refresh_token": token.refresh_token,
            }
        ).json()

        token.access_token = response["access_token"]
        token.expires_at = timezone.now() + timedelta(seconds=response["expires_in"])
        token.save()

    return token.access_token


@login_required(login_url='/login/')
def sync_library(request):
    access_token = get_valid_token(request.user)
    headers = {"Authorization": f"Bearer {access_token}"}

    url = "https://api.spotify.com/v1/me/tracks?limit=50"
    total_saved = 0

    while url:
        response = requests.get(url, headers=headers).json()

        # Collect all artist IDs from this page for genre lookup
        artist_ids = []
        for item in response["items"]:
            artist_ids.append(item["track"]["artists"][0]["id"])

        # Fetch genres for all artists in one batch call (max 50)
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

        # Save each track
        for item in response["items"]:
            track = item["track"]
            primary_artist = track["artists"][0]

            Song.objects.update_or_create(
                spotify_id=track["id"],
                defaults={
                    "user": request.user,
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
            total_saved += 1

        # Move to next page
        url = response.get("next")

    return redirect('home')