from django.urls import path

from . import views

app_name = "images"

urlpatterns = [
    # Images
    path("", views.ImageListView.as_view(), name="list"),
    path("create/", views.ImageCreateView.as_view(), name="create"),
    path("upload/", views.ImageUploadView.as_view(), name="upload"),
    path(
        "detail/<int:id>/<slug:slug>/", views.ImageDetailView.as_view(), name="detail"
    ),
    path("like/", views.ImageLikeView.as_view(), name="like"),
    path("ranking/", views.ImageRankingView.as_view(), name="ranking"),
]
