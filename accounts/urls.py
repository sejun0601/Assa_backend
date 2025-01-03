from django.urls import path
from .views import GoogleLoginView, RegisterView, LoginView, LogoutView, LoginStatusView

urlpatterns = [
    path("social/google/", GoogleLoginView.as_view(), name="google_login"),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('status/', LoginStatusView.as_view(), name='login_status'),

]