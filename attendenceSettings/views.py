from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import *
from .serializers import *
from datetime import datetime
from .models import Attendance
from django.utils import timezone
from .service import AttendanceService, AttendanceReportService
from .utils import *

# Create your views here.

def create_default_actions():
    """Create default actions for the attendance system"""
    default_actions = [
        {"name": "Check In", "code": "check_in", "description": "Employee check-in"},
        {"name": "Check Out", "code": "check_out", "description": "Employee check-out"},
        {"name": "Break Start", "code": "break_start", "description": "Start of break time"},
        {"name": "Break End", "code": "break_end", "description": "End of break time"},
        {"name": "Lunch Start", "code": "lunch_start", "description": "Start of lunch break"},
        {"name": "Lunch End", "code": "lunch_end", "description": "End of lunch break"},
        {"name": "Half Day", "code": "half_day", "description": "Half day attendance"},
        {"name": "Work From Home", "code": "wfh", "description": "Work from home"},
        {"name": "Meeting", "code": "meeting", "description": "In meeting"},
        {"name": "Training", "code": "training", "description": "In training session"},
    ]
    
    for action_data in default_actions:
        Action.objects.get_or_create(
            code=action_data["code"],
            defaults={
                "name": action_data["name"],
                "description": action_data["description"],
                "is_active": True
            }
        )

#! Action views
class ActionListView(APIView):
    def get(self, request):
        actions = Action.objects.filter(is_deleted=False, is_active=True)
        serializer = ActionSerializer(actions, many=True)
        return Response({"data": serializer.data, "status": "200"})


class ActionCreateView(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = ActionSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ActionRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = Action.objects.get(pk=pk, is_deleted=False)
            serializer = ActionSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except Action.DoesNotExist:
            return Response({"error": "Action not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ActionUpdateView(APIView):
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = Action.objects.get(pk=pk, is_deleted=False)
                serializer = ActionSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Action.DoesNotExist:
            return Response({"error": "Action not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ActionDeleteView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = Action.objects.get(pk=pk, is_deleted=False)
                obj.is_deleted = True
                obj.save()
                return Response({"data": {"message": "Soft deleted"}, "status": "200"})
        except Action.DoesNotExist:
            return Response({"error": "Action not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


#! checkin and checkout

class AttendancePunchView(APIView):
    """
    Unified view for handling both check-in and check-out operations.
    Automatically updates the main Attendance model fields.
    """

    def post(self, request):
        try:
            with transaction.atomic():
                serializer = AttendancePunchSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response({"error": serializer.errors, "status": "500"})

                employee_id = serializer.validated_data["employee"]
                action_id = serializer.validated_data["action"]
                today = timezone.localdate()
                now_time = timezone.localtime().time()

                # Get the action object
                try:
                    action = Action.objects.get(id=action_id, is_active=True, is_deleted=False)
                except Action.DoesNotExist:
                    return Response({"error": "Action not found or inactive", "status": "500"})

                # Auto-set Present type if needed
                try:
                    present_type = AttendanceType.objects.get(code="P")
                except AttendanceType.DoesNotExist:
                    return Response({"error": "AttendanceType 'P' not found", "status": "500"})

                if action.code == "check_in":
                    return self._handle_check_in(employee_id, today, now_time, present_type, action)
                elif action.code == "check_out":
                    return self._handle_check_out(employee_id, today, now_time, present_type, action)
                elif action.code in ["break_start", "lunch_start"]:
                    return self._handle_break_start(employee_id, today, now_time, action)
                elif action.code in ["break_end", "lunch_end"]:
                    return self._handle_break_end(employee_id, today, now_time, action)
                elif action.code == "half_day":
                    return self._handle_half_day(employee_id, today, now_time, present_type, action)
                elif action.code == "wfh":
                    return self._handle_work_from_home(employee_id, today, now_time, present_type, action)
                else:
                    return self._handle_generic_action(employee_id, today, now_time, action)
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

    def _handle_check_in(self, employee_id, today, now_time, present_type, action):
        """Handle check-in logic with transaction safety"""
        with transaction.atomic():
            # Use select_for_update to prevent race conditions
            attendance, _ = Attendance.objects.select_for_update().get_or_create(
                employee=employee_id,
                date=today,
                defaults={"attendance_type": present_type}
            )

            if attendance.punches.filter(check_out_time__isnull=True).exists():
                return Response({"error": "Already checked in. Please check out first.", "status": "500"})

            # Create punch
            punch = AttendancePunch.objects.create(
                employee=employee_id,
                date=today,
                attendance=attendance,
                action=action,
                check_in_time=now_time
            )

            # Set check-in on main attendance model
            attendance.check_in_time = now_time

            # Set attendance type if not set
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
                "data": {
                    "message": "Check-in successful",
                    "action": action.name,
                    "action_id": action.id,
                    "check_in_time": str(punch.check_in_time),
                    "late_by_minutes": attendance.late_by_minutes or 0
                },
                "status": "200"
            })

    def _handle_check_out(self, employee_id, today, now_time, present_type, action):
        """Handle check-out logic with transaction safety"""
        with transaction.atomic():
            try:
                # Use select_for_update to prevent race conditions
                attendance = Attendance.objects.select_for_update().get(
                    employee=employee_id, date=today, is_deleted=False
                )
            except Attendance.DoesNotExist:
                return Response({"error": "No attendance found for today", "status": "500"})

            open_punch = attendance.punches.filter(check_out_time__isnull=True).last()
            if not open_punch:
                return Response({"error": "No open check-in found for today", "status": "500"})

            open_punch.check_out_time = now_time
            open_punch.save()

            # Set check-out on main attendance model
            attendance.check_out_time = now_time

            if not attendance.attendance_type:
                attendance.attendance_type = present_type

            # Calculate total worked minutes from all punches
            total_minutes = 0
            for punch in attendance.punches.all():
                if punch.check_in_time and punch.check_out_time:
                    in_time = datetime.combine(today, punch.check_in_time)
                    out_time = datetime.combine(today, punch.check_out_time)
                    total_minutes += max(0, int((out_time - in_time).total_seconds() / 60))

            # Calculate shift minutes (default 480 or from sub_shift)
            shift_minutes = 480
            if attendance.sub_shift and attendance.sub_shift.time_end and attendance.sub_shift.time_start:
                start_dt = datetime.combine(today, attendance.sub_shift.time_start)
                end_dt = datetime.combine(today, attendance.sub_shift.time_end)
                shift_minutes = max(0, int((end_dt - start_dt).total_seconds() / 60))

            attendance.overtime_minutes = max(0, total_minutes - shift_minutes)
            attendance.save()

            return Response({
                "data": {
                    "message": "Check-out successful",
                    "action": action.name,
                    "action_id": action.id,
                    "check_out_time": str(open_punch.check_out_time),
                    "worked_minutes_today": total_minutes,
                    "overtime_minutes": attendance.overtime_minutes
                },
                "status": "200"
            })

    def _handle_generic_action(self, employee_id, today, now_time, action):
        """Handle other actions like breaks with transaction safety"""
        with transaction.atomic():
            try:
                attendance = Attendance.objects.select_for_update().get(
                    employee=employee_id, date=today, is_deleted=False
                )
            except Attendance.DoesNotExist:
                return Response({"error": "No attendance found for today", "status": "500"})

            punch = AttendancePunch.objects.create(
                employee=employee_id,
                date=today,
                attendance=attendance,
                action=action,
                check_in_time=now_time
            )

            return Response({
                "data": {
                    "message": f"{action.name} successful",
                    "action": action.name,
                    "action_id": action.id,
                    "action_time": str(punch.check_in_time)
                },
                "status": "200"
            })

    def _handle_break_start(self, employee_id, today, now_time, action):
        """Handle break start (lunch or regular break) with transaction safety"""
        with transaction.atomic():
            try:
                attendance = Attendance.objects.select_for_update().get(
                    employee=employee_id, date=today, is_deleted=False
                )
            except Attendance.DoesNotExist:
                return Response({"error": "No attendance found for today", "status": "500"})

            # Check if already on break
            open_break = attendance.punches.filter(
                action__code__in=["break_start", "lunch_start"],
                check_out_time__isnull=True
            ).exists()
            
            if open_break:
                return Response({"error": f"Already on {action.name.lower()}", "status": "500"})

            # Create break punch
            punch = AttendancePunch.objects.create(
                employee=employee_id,
                date=today,
                attendance=attendance,
                action=action,
                check_in_time=now_time
            )

            return Response({
                "data": {
                    "message": f"{action.name} started",
                    "action": action.name,
                    "action_id": action.id,
                    "break_start_time": str(punch.check_in_time)
                },
                "status": "200"
            })

    def _handle_break_end(self, employee_id, today, now_time, action):
        """Handle break end (lunch or regular break) with transaction safety"""
        with transaction.atomic():
            try:
                attendance = Attendance.objects.select_for_update().get(
                    employee=employee_id, date=today, is_deleted=False
                )
            except Attendance.DoesNotExist:
                return Response({"error": "No attendance found for today", "status": "500"})

            # Find open break
            if action.code == "break_end":
                open_break = attendance.punches.filter(
                    action__code="break_start",
                    check_out_time__isnull=True
                ).last()
            else:  # lunch_end
                open_break = attendance.punches.filter(
                    action__code="lunch_start",
                    check_out_time__isnull=True
                ).last()

            if not open_break:
                return Response({"error": f"No open {action.name.lower()} found", "status": "500"})

            # Close the break
            open_break.check_out_time = now_time
            open_break.save()

            # Calculate break duration
            break_duration = int((datetime.combine(today, now_time) - 
                                 datetime.combine(today, open_break.check_in_time)).total_seconds() / 60)

            return Response({
                "data": {
                    "message": f"{action.name} ended",
                    "action": action.name,
                    "action_id": action.id,
                    "break_end_time": str(now_time),
                    "break_duration_minutes": break_duration
                },
                "status": "200"
            })

    def _handle_half_day(self, employee_id, today, now_time, present_type, action):
        """Handle half day attendance with transaction safety"""
        with transaction.atomic():
            attendance, _ = Attendance.objects.select_for_update().get_or_create(
                employee=employee_id,
                date=today,
                defaults={"attendance_type": present_type}
            )

            # Create half day punch
            punch = AttendancePunch.objects.create(
                employee=employee_id,
                date=today,
                attendance=attendance,
                action=action,
                check_in_time=now_time
            )

            # Set attendance type to half day
            try:
                half_day_type = AttendanceType.objects.get(code="HD")
                attendance.attendance_type = half_day_type
            except AttendanceType.DoesNotExist:
                # If no half day type exists, keep present type
                pass

            attendance.save()

            return Response({
                "data": {
                    "message": "Half day marked successfully",
                    "action": action.name,
                    "action_id": action.id,
                    "half_day_time": str(punch.check_in_time)
                },
                "status": "200"
            })

    def _handle_work_from_home(self, employee_id, today, now_time, present_type, action):
        """Handle work from home attendance with transaction safety"""
        with transaction.atomic():
            attendance, _ = Attendance.objects.select_for_update().get_or_create(
                employee=employee_id,
                date=today,
                defaults={"attendance_type": present_type}
            )

            # Create WFH punch
            punch = AttendancePunch.objects.create(
                employee=employee_id,
                date=today,
                attendance=attendance,
                action=action,
                check_in_time=now_time
            )

            # Set attendance type to WFH
            try:
                wfh_type = AttendanceType.objects.get(code="WFH")
                attendance.attendance_type = wfh_type
            except AttendanceType.DoesNotExist:
                # If no WFH type exists, keep present type
                pass

            attendance.save()

            return Response({
                "data": {
                    "message": "Work from home marked successfully",
                    "action": action.name,
                    "action_id": action.id,
                    "wfh_time": str(punch.check_in_time)
                },
                "status": "200"
            })

    def get(self, request):
        """Check if employee is currently checked in"""
        employee_id = request.query_params.get("employee")
        if not employee_id:
            return Response({"error": "employee parameter is required", "status": "500"})

        today = timezone.localdate()

        try:
            attendance = Attendance.objects.get(employee=employee_id, date=today, is_deleted=False)
            open_punch = attendance.punches.filter(check_out_time__isnull=True).last()

            return Response({
                "data": {
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
                },
                "status": "200"
            })
        except Attendance.DoesNotExist:
            return Response({
                "data": {
                    "employee": employee_id,
                    "date": str(today),
                    "is_checked_in": False,
                    "current_punch": None,
                    "total_punches_today": 0,
                    "worked_minutes_today": 0
                },
                "status": "200"
            })

#! attendance type
class AttendanceTypeListView(APIView):
    def get(self, request):
        types = AttendanceType.objects.filter(is_deleted=False)
        serializer = AttendanceTypeSerializer(types, many=True)
        return Response({"data": serializer.data, "status": "200"})


class AttendanceTypeCreateView(APIView):
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
    def get(self, request, pk):
        try:
            obj = AttendanceType.objects.get(pk=pk, is_deleted=False)
            serializer = AttendanceTypeSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance Type not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class AttendanceTypeUpdateView(APIView):
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = AttendanceType.objects.get(pk=pk, is_deleted=False)
                serializer = AttendanceTypeSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance Type not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class AttendanceTypeDeleteView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = AttendanceType.objects.get(pk=pk, is_deleted=False)
                obj.is_deleted = True
                obj.save()
                return Response({"data": {"message": "Soft deleted"}, "status": "200"})
        except AttendanceType.DoesNotExist:
            return Response({"error": "Attendance Type not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


#! attendance
class AttendanceListView(APIView):
    def get(self, request):
        employee_id = request.query_params.get("employee_id")
        queryset = Attendance.objects.filter(is_deleted=False)
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        serializer = AttendanceSerializer(queryset, many=True)
        return Response({"data": serializer.data, "status": "200"})


class AttendanceCreateView(APIView):
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
    def get(self, request, pk):
        try:
            obj = Attendance.objects.get(pk=pk, is_deleted=False)
            serializer = AttendanceSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class AttendanceUpdateView(APIView):
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = Attendance.objects.get(pk=pk, is_deleted=False)
                serializer = AttendanceSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class AttendanceDeleteView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = Attendance.objects.get(pk=pk, is_deleted=False)
                obj.is_deleted = True
                obj.save()
                return Response({"data": {"message": "Soft deleted"}, "status": "200"})
        except Attendance.DoesNotExist:
            return Response({"error": "Attendance not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})