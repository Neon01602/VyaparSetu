from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('vendor/', views.vendor_auth, name='vendor'),
    path('investor/', views.investor_auth, name='investor'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("vendor/verify/<uuid:uid>/", views.vendor_verify, name="vendor_verify"),
path('vendor/invest/<str:short_uid>/', views.invest_vendor, name='invest_vendor'),
path("logout/", views.logout_view, name="logout"),
path('my-investments/', views.investor_investments, name='investor_investments'),
]
