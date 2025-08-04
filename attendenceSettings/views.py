from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from datetime import datetime, time
from .models import *
from .serializers import *
from .service import AttendanceService, AttendanceReportService, LeaveService
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
                
                result = LeaveService.update_leave_balance(employee_id, leave_type_id, adjustment_days, year)
                return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

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
    """Unified view for all attendance actions (check-in, check-out, breaks, etc.)"""
    
    def post(self, request):
        """Process attendance punch (check-in, check-out, breaks, etc.)"""
        try:
            with transaction.atomic():
                serializer = AttendancePunchSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"error": serializer.errors, "status": "500"})
                
                # Extract data
                employee_id = serializer.validated_data["employee"]
                action_type = serializer.validated_data["action_type"]
                source_id = serializer.validated_data.get("source_id")  # Optional
                remarks = serializer.validated_data.get("remarks", "")  # Optional
                today = timezone.localdate()
                now_time = timezone.localtime()
                
                # Get present attendance type
                try:
                    present_type = AttendanceType.objects.get(code="P", deleted=False)
                except AttendanceType.DoesNotExist:
                    return Response({"error": "Present attendance type not found", "status": "500"})
                
                # Route to appropriate service method based on action type
                if action_type == "check_in":
                    result = AttendanceService.process_check_in(employee_id, action_type, today, now_time, present_type, source_id, remarks)
                elif action_type == "check_out":
                    result = AttendanceService.process_check_out(employee_id, action_type, today, now_time, present_type, source_id, remarks)
                elif action_type in ["break_start", "lunch_start"]:
                    result = AttendanceService.process_break_start(employee_id, action_type, today, now_time, source_id, remarks)
                elif action_type in ["break_end", "lunch_end"]:
                    result = AttendanceService.process_break_end(employee_id, action_type, today, now_time, source_id, remarks)
                elif action_type == "half_day":
                    result = AttendanceService.process_half_day(employee_id, action_type, today, now_time, present_type, source_id, remarks)
                elif action_type == "wfh":
                    result = AttendanceService.process_work_from_home(employee_id, action_type, today, now_time, present_type, source_id, remarks)
                else:
                    result = AttendanceService.process_generic_action(employee_id, action_type, today, now_time, source_id, remarks)
                
                return Response({"data": result, "status": "200"})
                
        except Exception as e:
            return Response({"error": str(e), "status": "500"})
    
    def get(self, request):
        """Check if employee is currently checked in"""
        try:
            employee_id = request.data.get("employee")
            if not employee_id:
                return Response({"error": "employee parameter is required", "status": "500"})
            
            today = timezone.localdate()
            result = AttendanceReportService.get_employee_attendance_summary(employee_id, today)
            return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

# ATTENDANCE REPORTING VIEWS

class AttendanceReportView(APIView):
    """Generate attendance reports"""
    def post(self, request):
        try:
            with transaction.atomic():
                employee_id = request.data.get('employee')
                start_date = request.data.get('start_date')
                end_date = request.data.get('end_date')
                
                result = AttendanceReportService.get_attendance_report(employee_id, start_date, end_date)
                return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class EmployeeStatusView(APIView):
    """Get current employee status"""
    def post(self, request):
        try:
            employee_id = request.data.get('employee')
            if not employee_id:
                return Response({"error": "employee parameter is required", "status": "500"})
            
            today = timezone.localdate()
            result = AttendanceReportService.get_employee_status(employee_id, today)
            return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

class AutoMarkAbsentView(APIView):
    """Auto mark absent for employees"""
    def post(self, request):
        try:
            with transaction.atomic():
                date = request.data.get('date', timezone.localdate())
                result = AttendanceReportService.auto_mark_absent_service(date)
                return Response({"data": result, "status": "200"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})