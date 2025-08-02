from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from datetime import datetime
from .models import Attendance
from django.utils import timezone
from .service import *

# Create your views here.

#! Action views
class ActionListView(APIView):
    def get(self, request):
        actions = Action.objects.filter(is_deleted=False, is_active=True)
        serializer = ActionSerializer(actions, many=True)
        return Response(serializer.data)


class ActionCreateView(APIView):
    def post(self, request):
        serializer = ActionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ActionRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = Action.objects.get(pk=pk, is_deleted=False)
        except Action.DoesNotExist:
            return Response({"error": "Action not found"}, status=404)
        serializer = ActionSerializer(obj)
        return Response(serializer.data)


class ActionUpdateView(APIView):
    def put(self, request, pk):
        try:
            obj = Action.objects.get(pk=pk, is_deleted=False)
        except Action.DoesNotExist:
            return Response({"error": "Action not found"}, status=404)
        serializer = ActionSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ActionDeleteView(APIView):
    def delete(self, request, pk):
        try:
            obj = Action.objects.get(pk=pk, is_deleted=False)
        except Action.DoesNotExist:
            return Response({"error": "Action not found"}, status=404)
        obj.is_deleted = True
        obj.save()
        return Response({"message": "Soft deleted"}, status=200)


#! checkin and checkout

class AttendancePunchView(APIView):
    """
    Unified view for handling both check-in and check-out operations.
    More scalable and maintainable than separate views.
    """
    
    def post(self, request):
        serializer = AttendancePunchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        
        employee_id = serializer.validated_data["employee"]
        action_id = serializer.validated_data["action"]
        today = timezone.localdate()
        now_time = timezone.localtime().time()

        # Get the action object
        try:
            action = Action.objects.get(id=action_id, is_active=True, is_deleted=False)
        except Action.DoesNotExist:
            return Response({"error": "Action not found or inactive"}, status=400)

        # Auto-set Present type if needed
        try:
            present_type = AttendanceType.objects.get(code="P")
        except AttendanceType.DoesNotExist:
            return Response({"error": "AttendanceType 'P' not found"}, status=500)

        if action.code == "check_in":
            return self._handle_check_in(employee_id, today, now_time, present_type, action)
        elif action.code == "check_out":
            return self._handle_check_out(employee_id, today, now_time, present_type, action)
        else:
            return self._handle_generic_action(employee_id, today, now_time, action)

    def _handle_check_in(self, employee_id, today, now_time, present_type, action):
        """Handle check-in logic"""
        # Get or create today's attendance
        attendance, _ = Attendance.objects.get_or_create(
            employee=employee_id,
            date=today,
            defaults={"attendance_type": present_type}
        )

        # Prevent check-in if previous punch not closed
        if attendance.punches.filter(check_out_time__isnull=True).exists():
            return Response({"error": "Already checked in. Please check out first."}, status=400)

        # Create punch
        punch = AttendancePunch.objects.create(
            employee=employee_id,
            date=today,
            attendance=attendance,
            action=action,
            check_in_time=now_time
        )

        # Set attendance type if missing
        if not attendance.attendance_type:
            attendance.attendance_type = present_type

        # Calculate late_by_minutes
        if attendance.sub_shift and attendance.sub_shift.time_start:
            shift_start = datetime.combine(today, attendance.sub_shift.time_start)
            actual_in = datetime.combine(today, now_time)
            late_minutes = int((actual_in - shift_start).total_seconds() / 60)
            attendance.late_by_minutes = max(0, late_minutes)

        attendance.save()

        return Response({
            "message": "Check-in successful",
            "action": action.name,
            "action_id": action.id,
            "check_in_time": str(punch.check_in_time),
            "late_by_minutes": attendance.late_by_minutes or 0
        }, status=200)

    def _handle_check_out(self, employee_id, today, now_time, present_type, action):
        """Handle check-out logic"""
        # Get today's attendance
        try:
            attendance = Attendance.objects.get(employee=employee_id, date=today, is_deleted=False)
        except Attendance.DoesNotExist:
            return Response({"error": "No attendance found for today"}, status=404)

        # Find open punch (i.e., check-in done but no check-out)
        open_punch = attendance.punches.filter(check_out_time__isnull=True).last()
        if not open_punch:
            return Response({"error": "No open check-in found for today"}, status=400)

        # Close the punch
        open_punch.check_out_time = now_time
        open_punch.save()

        # Auto-set attendance type if not already set
        if not attendance.attendance_type:
            attendance.attendance_type = present_type

        # Calculate total worked minutes from all punches
        total_minutes = 0
        for punch in attendance.punches.all():
            if punch.check_in_time and punch.check_out_time:
                in_time = datetime.combine(today, punch.check_in_time)
                out_time = datetime.combine(today, punch.check_out_time)
                total_minutes += max(0, int((out_time - in_time).total_seconds() / 60))

        # Calculate overtime (default shift = 480 min, or from sub_shift)
        shift_minutes = 480
        if attendance.sub_shift and attendance.sub_shift.time_end and attendance.sub_shift.time_start:
            start_dt = datetime.combine(today, attendance.sub_shift.time_start)
            end_dt = datetime.combine(today, attendance.sub_shift.time_end)
            shift_minutes = max(0, int((end_dt - start_dt).total_seconds() / 60))

        attendance.overtime_minutes = max(0, total_minutes - shift_minutes)
        attendance.save()

        return Response({
            "message": "Check-out successful",
            "action": action.name,
            "action_id": action.id,
            "check_out_time": str(open_punch.check_out_time),
            "worked_minutes_today": total_minutes,
            "overtime_minutes": attendance.overtime_minutes
        }, status=200)

    def _handle_generic_action(self, employee_id, today, now_time, action):
        """Handle generic actions like break_start, break_end, etc."""
        # Get today's attendance
        try:
            attendance = Attendance.objects.get(employee=employee_id, date=today, is_deleted=False)
        except Attendance.DoesNotExist:
            return Response({"error": "No attendance found for today"}, status=404)

        # Create punch for the action
        punch = AttendancePunch.objects.create(
            employee=employee_id,
            date=today,
            attendance=attendance,
            action=action,
            check_in_time=now_time
        )

        return Response({
            "message": f"{action.name} successful",
            "action": action.name,
            "action_id": action.id,
            "action_time": str(punch.check_in_time)
        }, status=200)

    def get(self, request):
        """Get current punch status for an employee"""
        employee_id = request.query_params.get("employee")
        if not employee_id:
            return Response({"error": "employee parameter is required"}, status=400)

        today = timezone.localdate()
        
        try:
            attendance = Attendance.objects.get(employee=employee_id, date=today, is_deleted=False)
            open_punch = attendance.punches.filter(check_out_time__isnull=True).last()
            
            return Response({
                "employee": employee_id,
                "date": str(today),
                "is_checked_in": open_punch is not None,
                "current_punch": {
                    "check_in_time": str(open_punch.check_in_time) if open_punch else None,
                    "punch_id": open_punch.id if open_punch else None,
                    "action": open_punch.action.name if open_punch and open_punch.action else None
                },
                "total_punches_today": attendance.punches.count(),
                "worked_minutes_today": sum([
                    max(0, int((datetime.combine(today, punch.check_out_time) - 
                               datetime.combine(today, punch.check_in_time)).total_seconds() / 60))
                    for punch in attendance.punches.filter(check_out_time__isnull=False)
                ])
            })
        except Attendance.DoesNotExist:
            return Response({
                "employee": employee_id,
                "date": str(today),
                "is_checked_in": False,
                "current_punch": None,
                "total_punches_today": 0,
                "worked_minutes_today": 0
            })

#! attendance type
class AttendanceTypeListView(APIView):
    def get(self, request):
        types = AttendanceType.objects.filter(is_deleted=False)
        serializer = AttendanceTypeSerializer(types, many=True)
        return Response(serializer.data)


class AttendanceTypeCreateView(APIView):
    def post(self, request):
        serializer = AttendanceTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AttendanceTypeRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = AttendanceType.objects.get(pk=pk, is_deleted=False)
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance Type not found"}, status=404)
        serializer = AttendanceTypeSerializer(obj)
        return Response(serializer.data)


class AttendanceTypeUpdateView(APIView):
    def put(self, request, pk):
        try:
            obj = AttendanceType.objects.get(pk=pk, is_deleted=False)
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance Type not found"}, status=404)
        serializer = AttendanceTypeSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class AttendanceTypeDeleteView(APIView):
    def delete(self, request, pk):
        try:
            obj = AttendanceType.objects.get(pk=pk, is_deleted=False)
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance Type not found"}, status=404)
        obj.is_deleted = True
        obj.save()
        return Response({"message": "Soft deleted"}, status=200)


#! attendance
class AttendanceListView(APIView):
    def get(self, request):
        employee_id = request.query_params.get("employee_id")
        queryset = Attendance.objects.filter(is_deleted=False)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        serializer = AttendanceSerializer(queryset, many=True)
        return Response(serializer.data)


class AttendanceCreateView(APIView):
    def post(self, request):
        serializer = AttendanceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class AttendanceRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = Attendance.objects.get(pk=pk, is_deleted=False)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found"}, status=404)
        serializer = AttendanceSerializer(obj)
        return Response(serializer.data)


class AttendanceUpdateView(APIView):
    def put(self, request, pk):
        try:
            obj = Attendance.objects.get(pk=pk, is_deleted=False)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found"}, status=404)
        serializer = AttendanceSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class AttendanceDeleteView(APIView):
    def delete(self, request, pk):
        try:
            obj = Attendance.objects.get(pk=pk, is_deleted=False)
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found"}, status=404)
        obj.is_deleted = True
        obj.save()
        return Response({"message": "Soft deleted"}, status=200)