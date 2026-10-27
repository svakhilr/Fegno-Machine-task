from django.urls import path
from users.views import (
    UserRegisterView,
    OrganisationRegisterView,
    LoginView,
    UserLoginView,
    OrganisationLoginView,
)

urlpatterns = [
    # Registration
    path('register/user/', UserRegisterView.as_view(), name='user-register'),
    path('register/organisation/', OrganisationRegisterView.as_view(), name='organisation-register'),

    # Login (unified & role-specific)
    path('login/', LoginView.as_view(), name='login'),
    path('login/user/', UserLoginView.as_view(), name='user-login'),
    path('login/organisation/', OrganisationLoginView.as_view(), name='organisation-login'),
]
