from django.urls import path
from .views import *

urlpatterns = [
  # LEAVE REQUEST MANAGEMENT ENDPOINTS
  
    #leave requests
    path('list-leave-requests/', LeaveRequestListView.as_view()),                    
    path('create-leave-requests/', LeaveRequestCreateView.as_view()),               
    path('get-leave-requests/<int:pk>/', LeaveRequestRetrieveView.as_view()),      
    path('put-leave-requests/<int:pk>/', LeaveRequestUpdateView.as_view()),      
    path('delete-leave-requests/<int:pk>/', LeaveRequestDeleteView.as_view()),     
    
    #leave approval
    path('approve-leave-request/<int:pk>/', LeaveApprovalView.as_view()),     
    path('cancel-leave-request/<int:pk>/', LeaveCancellationView.as_view()),     
    
    #leave allocation
    path('leave-allocation/', LeaveAllocationListView.as_view(), name='leave-allocation'),
    path('create-leave-allocation/', LeaveAllocationCreateView.as_view(), name='create-leave-allocation'),
    path('get-leave-allocation/<int:pk>/', LeaveAllocationRetrieveView.as_view(), name='get-leave-allocation'),
    path('put-leave-allocation/<int:pk>/', LeaveAllocationUpdateView.as_view(), name='put-leave-allocation'),
    path('delete-leave-allocation/<int:pk>/', LeaveAllocationDeleteView.as_view(), name='delete-leave-allocation'),
    
    #leave balance
    path('leave-balance/', LeaveBalanceListView.as_view(), name='leave-balance'),
    path('create-leave-balance/', LeaveBalanceCreateView.as_view(), name='create-leave-balance'),
    path('get-leave-balance/<int:pk>/', LeaveBalanceRetrieveView.as_view(), name='get-leave-balance'),
    path('put-leave-balance/<int:pk>/', LeaveBalanceUpdateView.as_view(), name='put-leave-balance'),
    path('delete-leave-balance/<int:pk>/', LeaveBalanceDeleteView.as_view(), name='delete-leave-balance'),
    path('adjust-leave-balance/', LeaveBalanceAdjustmentView.as_view(), name='adjust-leave-balance'),

    #leave settings
    path('create-leave-settings/', LeaveSettingCreateView.as_view(), name='create-leave-settings'),

    #leave details
    path('leave-details/', LeaveDetailListView.as_view(), name='leave-details'),
    path('create-leave-detail/', LeaveDetailCreateView.as_view(), name='create-leave-detail'),
    path('get-leave-detail/<int:pk>/', LeaveDetailRetrieveView.as_view(), name='get-leave-detail'),
    path('put-leave-detail/<int:pk>/', LeaveDetailUpdateView.as_view(), name='put-leave-detail'),
    path('delete-leave-detail/<int:pk>/', LeaveDetailDeleteView.as_view(), name='delete-leave-detail'),
    path('leave-detail-attendance-types/', LeaveDetailAttendanceTypesView.as_view(), name='leave-detail-attendance-types'),
    
    #status management
    path('list-status/', StatusListView.as_view(), name='list-status'),
    path('create-status/', StatusCreateView.as_view(), name='create-status'),
    path('get-status/<int:pk>/', StatusRetrieveView.as_view(), name='get-status'),
    path('put-status/<int:pk>/', StatusUpdateView.as_view(), name='put-status'),
    path('delete-status/<int:pk>/', StatusDeleteView.as_view(), name='delete-status'),

  
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
    
    #status management
    path('list-status/', StatusListView.as_view(), name='list-status'),
    path('create-status/', StatusCreateView.as_view(), name='create-status'),
    path('get-status/<int:pk>/', StatusRetrieveView.as_view(), name='get-status'),
    path('put-status/<int:pk>/', StatusUpdateView.as_view(), name='put-status'),
    path('delete-status/<int:pk>/', StatusDeleteView.as_view(), name='delete-status'),

  
    # ADDITIONAL UTILITY ENDPOINTS
  
    # Additional useful endpoints
    # path('employee-status/<int:employee_id>/', AttendancePunchView.as_view()),  # GET: Get employee current status
    # path('today-attendance/', AttendanceListView.as_view()),                    # GET: Get today's attendance records
    # path('employee-attendance/<int:employee_id>/', AttendanceListView.as_view()),  # GET: Get employee attendance history
]