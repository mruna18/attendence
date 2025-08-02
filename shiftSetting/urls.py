from django.urls import path
from .views import *

urlpatterns = [

    # Shift Head Types
    path('list-shift-head-types/', ShiftHeadTypeListView.as_view()),
    path('create-shift-head-types/', ShiftHeadTypeCreateView.as_view()),
    path('get-shift-head-types/<int:pk>/', ShiftHeadTypeRetrieveView.as_view()),
    path('put-shift-head-types/<int:pk>/', ShiftHeadTypeUpdateView.as_view()),
    path('delete-shift-head-types/<int:pk>', ShiftHeadTypeDeleteView.as_view()),

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
