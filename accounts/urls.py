# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path('login/', views.login_page, name='login_page'),
    path("spotify-login/", views.spotify_login, name="spotify_login"),
    path("callback/", views.spotify_callback, name="spotify_callback"),
    path('sync/', views.sync_library, name='sync_library'),
path("logout/", views.spotify_logout, name="logout"),

path('export/csv/',  views.export_csv,  name='export_csv'),
path('export/json/', views.export_json, name='export_json'),
path('export/txt/',  views.export_txt,  name='export_txt'),
path('export/md/',   views.export_md,   name='export_md'),
]


