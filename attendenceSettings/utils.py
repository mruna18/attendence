from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import *


# Time calculation utilities
def calculate_worked_minutes(attendance):
    """Calculate total worked minutes from attendance punches"""
    total_minutes = 0
    for punch in attendance.punches.all():
        if punch.check_in_time and punch.check_out_time:
            in_time = datetime.combine(attendance.date, punch.check_in_time)
            out_time = datetime.combine(attendance.date, punch.check_out_time)
            duration = int((out_time - in_time).total_seconds() / 60)
            total_minutes += max(0, duration)
    return total_minutes


def calculate_late_minutes(attendance, check_in_time):
    """Calculate late minutes based on shift start time"""
    if not attendance.sub_shift or not attendance.sub_shift.time_start:
        return 0
    
    shift_start = datetime.combine(attendance.date, attendance.sub_shift.time_start)
    actual_in = datetime.combine(attendance.date, check_in_time)
    late_minutes = int((actual_in - shift_start).total_seconds() / 60)
    return max(0, late_minutes)


def calculate_overtime_minutes(attendance, total_worked_minutes):
    """Calculate overtime minutes based on shift duration"""
    shift_minutes = 480  # Default 8 hours
    
    if attendance.sub_shift and attendance.sub_shift.time_end and attendance.sub_shift.time_start:
        start_dt = datetime.combine(attendance.date, attendance.sub_shift.time_start)
        end_dt = datetime.combine(attendance.date, attendance.sub_shift.time_end)
        shift_minutes = max(0, int((end_dt - start_dt).total_seconds() / 60))
    
    return max(0, total_worked_minutes - shift_minutes)


def calculate_break_duration(break_start_time, break_end_time, date):
    """Calculate break duration in minutes"""
    start_dt = datetime.combine(date, break_start_time)
    end_dt = datetime.combine(date, break_end_time)
    return int((end_dt - start_dt).total_seconds() / 60)


# Data validation utilities
def validate_employee_exists(employee_id):
    """Validate if employee exists"""
    # This would typically check against an Employee model
    # For now, we'll assume any positive integer is valid
    return employee_id > 0


def validate_action_exists(action_id):
    """Validate if action exists and is active"""
    try:
        action = Action.objects.get(id=action_id, is_active=True, is_deleted=False)
        return action
    except Action.DoesNotExist:
        return None


def validate_attendance_type_exists(code):
    """Validate if attendance type exists"""
    try:
        attendance_type = AttendanceType.objects.get(code=code, is_deleted=False)
        return attendance_type
    except AttendanceType.DoesNotExist:
        return None


# Response formatting utilities
def format_attendance_response(data, status="200"):
    """Format attendance response"""
    return {"data": data, "status": status}


def format_error_response(error_message, status="500"):
    """Format error response"""
    return {"error": error_message, "status": status}


def format_punch_response(message, action, action_id, time_field, time_value):
    """Format punch response"""
    return format_attendance_response({
        "message": message,
        "action": action,
        "action_id": action_id,
        time_field: str(time_value)
    })


# Database utility functions
def get_or_create_attendance(employee_id, date, default_type):
    """Get or create attendance record with transaction safety"""
    with transaction.atomic():
        attendance, created = Attendance.objects.select_for_update().get_or_create(
            employee=employee_id,
            date=date,
            defaults={"attendance_type": default_type}
        )
        return attendance, created


def create_attendance_punch(employee_id, date, attendance, action, check_in_time):
    """Create attendance punch record"""
    return AttendancePunch.objects.create(
        employee=employee_id,
        date=date,
        attendance=attendance,
        action=action,
        check_in_time=check_in_time
    )


def get_open_punch(attendance):
    """Get the latest open punch for an attendance"""
    return attendance.punches.filter(check_out_time__isnull=True).last()


def get_employee_ids():
    """Get all employee IDs from attendance records"""
    return Attendance.objects.values_list('employee', flat=True).distinct()


# Business logic utilities
def auto_mark_absent():
    """Auto-mark absent for employees not present today"""
    today = timezone.localdate()
    all_employee_ids = get_employee_ids()
    present_today = Attendance.objects.filter(date=today).values_list("employee", flat=True)

    for emp_id in all_employee_ids:
        if emp_id not in present_today:
            absent_type = validate_attendance_type_exists("A")
            if absent_type:
                Attendance.objects.create(
                    employee=emp_id,
                    date=today,
                    attendance_type=absent_type,
                    remarks="Auto-marked absent"
                )


def check_duplicate_punch(attendance, action_code):
    """Check if employee already has an open punch for this action"""
    return attendance.punches.filter(
        action__code=action_code,
        check_out_time__isnull=True
    ).exists()


def get_attendance_summary(employee_id, date):
    """Get attendance summary for employee on specific date"""
    try:
        attendance = Attendance.objects.get(
            employee=employee_id, 
            date=date, 
            is_deleted=False
        )
        
        open_punch = get_open_punch(attendance)
        total_punches = attendance.punches.count()
        worked_minutes = calculate_worked_minutes(attendance)
        
        return {
            "employee": employee_id,
            "date": str(date),
            "is_checked_in": open_punch is not None,
            "current_punch": {
                "check_in_time": str(open_punch.check_in_time) if open_punch else None,
                "punch_id": open_punch.id if open_punch else None,
                "action": open_punch.action.name if open_punch and open_punch.action else None
            },
            "total_punches_today": total_punches,
            "worked_minutes_today": worked_minutes
        }
    except Attendance.DoesNotExist:
        return {
            "employee": employee_id,
            "date": str(date),
            "is_checked_in": False,
            "current_punch": None,
            "total_punches_today": 0,
            "worked_minutes_today": 0
        } 