from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import datetime, time
from .models import *
from .serializers import *
from .service import AttendanceService, LeaveService
from .utils import *

# LEAVE REQUEST MANAGEMENT VIEWS
class LeaveRequestListView(APIView):
    """List all leave requests"""
    def get(self, request):
        try:
            leave_requests = LeaveRequest.objects.filter(deleted=False)
            serializer = LeaveRequestSerializer(leave_requests, many=True)
            return Response({"data": serializer.data, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveRequestCreateView(APIView):
    """Create a new leave request"""
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = LeaveRequestSerializer(data=request.data)
                if serializer.is_valid():
                    result = LeaveService.create_leave_request(serializer.validated_data)
                    return Response({"data": result, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveRequestRetrieveView(APIView):
    """Get a specific leave request by ID"""
    def get(self, request, pk):
        try:
            obj = LeaveRequest.objects.get(pk=pk, deleted=False)
            serializer = LeaveRequestSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except LeaveRequest.DoesNotExist:
            return Response({"error": "Leave request not found", "status": "500"})

class LeaveRequestUpdateView(APIView):
    """Update a leave request"""
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = LeaveRequest.objects.get(pk=pk, deleted=False)
                serializer = LeaveRequestSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except LeaveRequest.DoesNotExist:
            return Response({"error": "Leave request not found", "status": "500"})

class LeaveRequestDeleteView(APIView):
    """Soft delete a leave request"""
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = LeaveRequest.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Leave request deleted successfully", "status": "200"})
        except LeaveRequest.DoesNotExist:
            return Response({"error": "Leave request not found", "status": "500"})

class LeaveApprovalView(APIView):
    """Approve or reject a leave request"""
    def post(self, request, pk):
        try:
            with transaction.atomic():
                action = request.data.get('action')  # 'approve' or 'reject'
                remarks = request.data.get('remarks', '')
                approver_id = request.data.get('approved_by')
                
                if action == 'approve':
                    result = LeaveService.approve_leave_request(pk, approver_id, remarks)
                elif action == 'reject':
                    result = LeaveService.reject_leave_request(pk, approver_id, remarks)
                else:
                    return Response({"error": "Invalid action. Use 'approve' or 'reject'", "status": "500"})
                
                return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveCancellationView(APIView):
    """Cancel a leave request"""
    def post(self, request, pk):
        try:
            with transaction.atomic():
                result = LeaveService.cancel_leave_request(pk)
                return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

# LEAVE ALLOCATION MANAGEMENT VIEWS

class LeaveAllocationListView(APIView):
    """List all leave allocations"""
    def get(self, request):
        try:
            leave_allocations = LeaveAllocation.objects.filter(deleted=False)
            serializer = LeaveAllocationSerializer(leave_allocations, many=True)
            return Response({"data": serializer.data, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveAllocationCreateView(APIView):
    """Create a new leave allocation"""
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = LeaveAllocationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveAllocationRetrieveView(APIView):
    """Get a specific leave allocation by ID"""
    def get(self, request, pk):
        try:
            obj = LeaveAllocation.objects.get(pk=pk, deleted=False)
            serializer = LeaveAllocationSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except LeaveAllocation.DoesNotExist:
            return Response({"error": "Leave allocation not found", "status": "500"})

class LeaveAllocationUpdateView(APIView):
    """Update a leave allocation"""
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = LeaveAllocation.objects.get(pk=pk, deleted=False)
                serializer = LeaveAllocationSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except LeaveAllocation.DoesNotExist:
            return Response({"error": "Leave allocation not found", "status": "500"})

class LeaveAllocationDeleteView(APIView):
    """Soft delete a leave allocation"""
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = LeaveAllocation.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Leave allocation deleted successfully", "status": "200"})
        except LeaveAllocation.DoesNotExist:
            return Response({"error": "Leave allocation not found", "status": "500"})


# LEAVE BALANCE MANAGEMENT VIEWS

class LeaveBalanceListView(APIView):
    """List all leave balances"""
    def get(self, request):
        try:
            leave_balances = LeaveBalance.objects.filter(deleted=False)
            serializer = LeaveBalanceSerializer(leave_balances, many=True)
            return Response({"data": serializer.data, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveBalanceCreateView(APIView):
    """Create a new leave balance"""
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = LeaveBalanceSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class LeaveBalanceRetrieveView(APIView):
    """Get a specific leave balance by ID"""
    def get(self, request, pk):
        try:
            obj = LeaveBalance.objects.get(pk=pk, deleted=False)
            serializer = LeaveBalanceSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except LeaveBalance.DoesNotExist:
            return Response({"error": "Leave balance not found", "status": "500"})

class LeaveBalanceUpdateView(APIView):
    """Update a leave balance"""
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = LeaveBalance.objects.get(pk=pk, deleted=False)
                serializer = LeaveBalanceSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except LeaveBalance.DoesNotExist:
            return Response({"error": "Leave balance not found", "status": "500"})

class LeaveBalanceDeleteView(APIView):
    """Soft delete a leave balance"""
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = LeaveBalance.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Leave balance deleted successfully", "status": "200"})
        except LeaveBalance.DoesNotExist:
            return Response({"error": "Leave balance not found", "status": "500"})

class LeaveBalanceAdjustmentView(APIView):
    """Adjust leave balance for an employee"""
    def post(self, request):
        try:
            with transaction.atomic():
                employee_id = request.data.get('employee')
                leave_type_id = request.data.get('leave_type')
                adjustment_days = request.data.get('adjustment_days', 0)
                year = request.data.get('year', timezone.now().year)
                
                LeaveService.update_leave_balance(employee_id, leave_type_id, adjustment_days, year)
                result = {"message": f"Leave balance adjusted by {adjustment_days} days"}
                return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


# LEAVE BALANCE MAPPING MANAGEMENT VIEWS

class LeaveSettingCreateView(APIView):
    """
    Create leave settings for an employee for a financial year.
    """

    def post(self, request):
        try:
            data = request.data
            employee = data.get("employee")
            company = data.get("company")
            start_date = data.get("financial_year_start")
            end_date = data.get("financial_year_end")
            allocations = data.get("leave_allocation", [])

            if not all([employee, company, start_date, end_date, allocations]):
                return Response({"error": "Missing required fields", "status": 400})

            with transaction.atomic():
                created_settings = []

                for entry in allocations:
                    attendance_type_id = entry.get("attendance_type_id")
                    allotted_days = entry.get("allotted_days", 0)

                    if not attendance_type_id:
                        return Response({"error": "attendance_type_id is required", "status": 400})

                    try:
                        attendance_type = AttendanceType.objects.get(id=attendance_type_id, deleted=False)
                    except AttendanceType.DoesNotExist:
                        return Response({"error": f"AttendanceType ID {attendance_type_id} not found", "status": 404})

                    leave_setting, _ = LeaveSetting.objects.update_or_create(
                        employee=employee,
                        company=company,
                        attendance_type=attendance_type,
                        financial_year_start=start_date,
                        defaults={
                            "financial_year_end": end_date,
                            "allotted_days": allotted_days,
                            "deleted": False
                        }
                    )
                    created_settings.append(leave_setting)

                serializer = LeaveSettingSerializer(created_settings, many=True)
                return Response({"data": serializer.data, "status": "200"})

        except Exception as e:
            return Response({"error": str(e), "status": 500})
        


# STATUS MANAGEMENT VIEWS

class StatusListView(APIView):
    """List all status types"""
    def get(self, request):
        try:
            status_types = Status.objects.filter(deleted=False)
            serializer = StatusSerializer(status_types, many=True)
            return Response({"data": serializer.data, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class StatusCreateView(APIView):
    """Create a new status type"""
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = StatusSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class StatusRetrieveView(APIView):
    """Get a specific status type by ID"""
    def get(self, request, pk):
        try:
            obj = Status.objects.get(pk=pk, deleted=False)
            serializer = StatusSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except Status.DoesNotExist:
            return Response({"error": "Status type not found", "status": "500"})

class StatusUpdateView(APIView):
    """Update a status type"""
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = Status.objects.get(pk=pk, deleted=False)
                serializer = StatusSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Status.DoesNotExist:
            return Response({"error": "Status type not found", "status": "500"})

class StatusDeleteView(APIView):
    """Soft delete a status type"""
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = Status.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Status type deleted successfully", "status": "200"})
        except Status.DoesNotExist:
            return Response({"error": "Status type not found", "status": "500"})


# ATTENDANCE TYPE MANAGEMENT VIEWS

class AttendanceTypeListView(APIView):
    """List all attendance types"""
    def get(self, request):
        try:
            attendance_types = AttendanceType.objects.filter(deleted=False)
            serializer = AttendanceTypeSerializer(attendance_types, many=True)
            return Response({"data": serializer.data, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class AttendanceTypeCreateView(APIView):
    """Create a new attendance type"""
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = AttendanceTypeSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class AttendanceTypeRetrieveView(APIView):
    """Get a specific attendance type by ID"""
    def get(self, request, pk):
        try:
            obj = AttendanceType.objects.get(pk=pk, deleted=False)
            serializer = AttendanceTypeSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance type not found", "status": "500"})

class AttendanceTypeUpdateView(APIView):
    """Update an attendance type"""
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = AttendanceType.objects.get(pk=pk, deleted=False)
                serializer = AttendanceTypeSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance type not found", "status": "500"})

class AttendanceTypeDeleteView(APIView):
    """Soft delete an attendance type"""
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = AttendanceType.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Attendance type deleted successfully", "status": "200"})
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance type not found", "status": "500"})

# ATTENDANCE MANAGEMENT VIEWS

class AttendanceListView(APIView):
    """List all attendance records"""
    def get(self, request):
        try:
            attendance_records = Attendance.objects.filter(deleted=False)
            serializer = AttendanceSerializer(attendance_records, many=True)
            return Response({"data": serializer.data, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class AttendanceCreateView(APIView):
    """Create a new attendance record"""
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = AttendanceSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class AttendanceRetrieveView(APIView):
    """Get a specific attendance record by ID"""
    def get(self, request, pk):
        try:
            obj = Attendance.objects.get(pk=pk, deleted=False)
            serializer = AttendanceSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance record not found", "status": "500"})

class AttendanceUpdateView(APIView):
    """Update an attendance type"""
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = Attendance.objects.get(pk=pk, deleted=False)
                serializer = AttendanceSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance record not found", "status": "500"})

class AttendanceDeleteView(APIView):
    """Soft delete an attendance record"""
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = Attendance.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Attendance record deleted successfully", "status": "200"})
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance record not found", "status": "500"})

# UNIFIED ATTENDANCE PUNCH VIEW

class AttendancePunchView(APIView):
    """Unified view for attendance check-in and check-out with working hours tracking"""
    
    def post(self, request):
        """Process attendance punch (check-in or check-out)"""
        try:
            with transaction.atomic():
                serializer = AttendancePunchSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"error": serializer.errors, "status": "500"})
                
                # Extract data
                employee_id = serializer.validated_data["employee"]
                action_type_id = serializer.validated_data["action_type"]
                source_id = serializer.validated_data.get("source_id")  # Optional
                remarks = serializer.validated_data.get("remarks", "")  # Optional
                custom_timestamp = serializer.validated_data.get("custom_timestamp")  # Optional
                
                # Use the simplified service method
                result = AttendanceService.process_attendance_punch(
                    employee_id=employee_id,
                    action_type_id=action_type_id,
                    source_id=source_id,
                    remarks=remarks,
                    custom_timestamp=custom_timestamp
                )
                
                # Check if result is an error
                if "error" in result:
                    return Response({"error": result["error"], "status": "400"})
                
                return Response({"data": result, "status": "200"})
                
        except Exception as e:
           
            return Response({"error": str(e), "status": "500"})
    
    def get(self, request):
        """Get employee's current attendance status for today"""
        try:
            employee_id = request.query_params.get("employee")
            if not employee_id:
                return Response({"error": "employee parameter is required", "status": "400"})
            
            # Use the service method to get employee status
            result = AttendanceService.get_employee_attendance_status(employee_id)
            
            # Check if result is an error
            if "error" in result:
                return Response({"error": result["error"], "status": "500"})
            
            return Response({"data": result, "status": "200"})
                
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

