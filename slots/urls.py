from django.urls import path
from .views import (
    WeeklySlotsAPIView,
    BookSlotAPIView,
    CancelBookingAPIView,
    RegisterAPIView,
    AdminSlotsAPIView,
)
from .views import current_user
from .views import AdminCreateSlotAPIView

urlpatterns = [
    # Slot APIs
    path('slots/', WeeklySlotsAPIView.as_view(), name='weekly-slots'),
    path('slots/<int:slot_id>/book/', BookSlotAPIView.as_view(), name='book-slot'),
    path('slots/<int:slot_id>/cancel/', CancelBookingAPIView.as_view(), name='cancel-slot'),

    # Admin API
    path('admin/slots/', AdminSlotsAPIView.as_view(), name='admin-slots'),
    path('admin/slots/add/', AdminCreateSlotAPIView.as_view(), name='admin-add-slot'),

    # User registration
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('current_user/', current_user, name='current-user'),
]
