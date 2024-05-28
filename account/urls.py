from django.urls import path

from . import views

urlpatterns = [
    # path('', include('django.contrib.auth.urls')),
    # Login/Logout view
    # path('login/', auth_views.LoginView.as_view(), name='login'),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.UserLogoutView.as_view(), name="logout"),
    # Password Change View
    path(
        "password-change/",
        views.UserPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password-change/done/",
        views.UserPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    # Password Reset View
    path(
        "password-reset/", views.UserPasswordResetView.as_view(), name="password_reset"
    ),
    path(
        "password-reset/done/",
        views.UserPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "password-reset/<uidb64>/<token>/",
        views.UserPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset/complete/",
        views.UserPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    # Dashboard
    path("", views.DashboardView.as_view(), name="dashboard"),
    # Register View
    path("register/", views.UserRegisterView.as_view(), name="register"),
    # Account activation view
    path(
        "activate/<uidb64>/<token>/",
        views.UserActivateView.as_view(),
        name="activate",
    ),
    # Account Edit
    path("edit/", views.UserEditView.as_view(), name="edit"),
    # Users
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/follow/", views.UserFollowView.as_view(), name="user_follow"),
    path("users/<username>/", views.UserDetailView.as_view(), name="user_detail"),
]
