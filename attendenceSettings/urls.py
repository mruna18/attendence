from django.urls import path
from .views import *

urlpatterns = [
  
    # ACTION MANAGEMENT ENDPOINTS
  
    #actions
    path('list-actions/', ActionListView.as_view()),                    
    path('create-actions/', ActionCreateView.as_view()),               
    path('get-actions/<int:pk>/', ActionRetrieveView.as_view()),      
    path('put-actions/<int:pk>/', ActionUpdateView.as_view()),      
    path('delete-actions/<int:pk>/', ActionDeleteView.as_view()),     
    path('active-actions/', ActionListView.as_view()),                 

  
    #atttendance types
    path('list-attendance-types/', AttendanceTypeListView.as_view()),                    
    path('create-attendance-types/', AttendanceTypeCreateView.as_view()),               
    path('get-attendance-types/<int:pk>/', AttendanceTypeRetrieveView.as_view()),      
    path('put-attendance-types/<int:pk>/', AttendanceTypeUpdateView.as_view()),       
    path('delete-attendance-types/<int:pk>/', AttendanceTypeDeleteView.as_view()),     

  
    #attendance settings
    path('list-attendance/', AttendanceListView.as_view()),                   
    path('create-attendance/', AttendanceCreateView.as_view()),              
    path('get-attendance/<int:pk>/', AttendanceRetrieveView.as_view()),      
    path('put-attendance/<int:pk>/', AttendanceUpdateView.as_view()),        
    path('delete-attendance/<int:pk>/', AttendanceDeleteView.as_view()),     

  
    # Unified attendance punch - More scalable
    path('attendance-punch/', AttendancePunchView.as_view()),                
    
  
    # ADDITIONAL UTILITY ENDPOINTS
  
    # Additional useful endpoints
    # path('employee-status/<int:employee_id>/', AttendancePunchView.as_view()),  # GET: Get employee current status
    # path('today-attendance/', AttendanceListView.as_view()),                    # GET: Get today's attendance records
    # path('employee-attendance/<int:employee_id>/', AttendanceListView.as_view()),  # GET: Get employee attendance history
]