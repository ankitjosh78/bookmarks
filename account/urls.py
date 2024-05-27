from django.urls import path

from . import views

urlpatterns = [

    # path('', include('django.contrib.auth.urls')),
    # Login/Logout view
    # path('login/', auth_views.LoginView.as_view(), name='login'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),

    # Password Change View
    path('password-change/',
         views.UserPasswordChangeView.as_view(),
         name='password_change'),
    path('password-change/done/',
         views.UserPasswordChangeDoneView.as_view(),
         name='password_change_done'),

    # Password Reset View
    path('password-reset/',
         views.UserPasswordResetView.as_view(),
         name='password_reset'),
    path('password-reset/done/',
         views.UserPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         views.UserPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         views.UserPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Register View
    path('register/', views.register, name='register'),

    # Account activation view
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    
    # Account Edit
    path('edit/', views.edit, name='edit'),
    
    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/follow/', views.user_follow, name='user_follow'),
    path('users/<username>/', views.user_detail, name='user_detail'),
]
