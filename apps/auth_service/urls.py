from django.urls import path
from . import views

urlpatterns = [
    path('device',         views.DeviceAuthView.as_view(),       name='auth-device'),
    path('phone/link',     views.PhoneLinkView.as_view(),        name='auth-phone-link'),
    path('phone/verify',   views.OTPVerifyView.as_view(),        name='auth-phone-verify'),
    path('phone/login',    views.PhoneLoginView.as_view(),       name='auth-phone-login'),
    path('phone/confirm',  views.PhoneLoginVerifyView.as_view(), name='auth-phone-confirm'),
    path('refresh',        views.TokenRefreshView.as_view(),     name='auth-refresh'),
    path('logout',         views.LogoutView.as_view(),           name='auth-logout'),
]
