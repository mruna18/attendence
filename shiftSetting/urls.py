from django.urls import path
from .views import *

urlpatterns = [

    # Shifts
    path('list-shifts/', ShiftListView.as_view()),
    path('create-shifts/', ShiftCreateView.as_view()),
    path('get-shifts/<int:pk>/', ShiftRetrieveView.as_view()),
    path('put-shifts/<int:pk>/', ShiftUpdateView.as_view()),
    path('delete-shifts/<int:pk>', ShiftDeleteView.as_view()),

    # SubShifts
    path('list-subshifts/', SubShiftListView.as_view()),
    path('create-subshifts/', SubShiftCreateView.as_view()),
    path('get-subshifts/<int:pk>/', SubShiftRetrieveView.as_view()),
    path('put-subshifts/<int:pk>/', SubShiftUpdateView.as_view()),
    path('delete-subshifts/<int:pk>', SubShiftDeleteView.as_view()),
]
