from datetime import datetime, timedelta, time
from django.utils import timezone
from django.db import transaction
from .models import *


# Time calculation utilities
def calculate_worked_minutes(attendance):
    """Calculate total worked minutes from attendance record"""
    if not attendance.date_check_in or not attendance.date_check_out:
        return 0
    
    time_diff = attendance.date_check_out - attendance.date_check_in
    return int(time_diff.total_seconds() / 60)


def calculate_working_hours(attendance):
    """Calculate working hours from attendance record"""
    if not attendance.date_check_in or not attendance.date_check_out:
        return 0
    
    time_diff = attendance.date_check_out - attendance.date_check_in
    working_hours = time_diff.total_seconds() / 3600  # Convert to hours
    return round(working_hours, 2)


def calculate_late_minutes(attendance, check_in_time, grace_period_minutes=15):
    """Calculate late minutes based on shift start time with grace period"""
    try:
        # If no sub_shift or time_start, return 0
        if not attendance.sub_shift or not attendance.sub_shift.time_start:
            return 0
        
        # Get current date from check_in_time
        if hasattr(check_in_time, 'date'):
            current_date = check_in_time.date()
        else:
            current_date = timezone.localdate()
        
        # Convert check_in_time to datetime if it's a time object
        if isinstance(check_in_time, time):
            check_in_datetime = datetime.combine(current_date, check_in_time)
        else:
            check_in_datetime = check_in_time
        
        # Handle night shifts (where end time < start time)
        shift_start_time = attendance.sub_shift.time_start
        shift_end_time = attendance.sub_shift.time_end
        
        # For night shifts, we need to determine the correct date for shift start
        # If shift end time is earlier than start time, it's a night shift
        if shift_end_time and shift_start_time and shift_end_time < shift_start_time:
            # This is a night shift (e.g., 18:00 to 02:00)
            # For check-in, use the same date as check-in time
            shift_start = datetime.combine(current_date, shift_start_time)
        else:
            # Regular day shift
            shift_start = datetime.combine(current_date, shift_start_time)
        
        shift_start = timezone.make_aware(shift_start)
        grace_period_end = shift_start + timedelta(minutes=grace_period_minutes)
        
        # Calculate late minutes (only if beyond grace period)
        if check_in_datetime > grace_period_end:
            late_minutes = int((check_in_datetime - grace_period_end).total_seconds() / 60)
            return max(0, late_minutes)
        return 0
    except Exception as e:
        # If any error occurs, return 0
        return 0


def validate_check_in_time(sub_shift, check_in_time, allow_early_check_in=True, early_buffer_minutes=30):
    """
    Validate if check-in time is within acceptable range for the sub-shift
    Returns: (is_valid, message, minutes_early)
    """
    try:
        if not sub_shift or not sub_shift.time_start:
            return True, "No shift timing defined", 0
        
        # Get current date
        current_date = timezone.localdate()
        
        # Convert check_in_time to datetime if it's a time object
        if isinstance(check_in_time, time):
            check_in_datetime = datetime.combine(current_date, check_in_time)
        else:
            check_in_datetime = check_in_time
        
        # Create shift start datetime
        shift_start = datetime.combine(current_date, sub_shift.time_start)
        
        # Calculate minutes early
        minutes_early = int((shift_start - check_in_datetime).total_seconds() / 60)
        
        if not allow_early_check_in and minutes_early > 0:
            return False, f"Check-in not allowed before shift start time ({sub_shift.time_start.strftime('%H:%M')})", minutes_early
        
        # Allow early check-in within buffer period
        if minutes_early > early_buffer_minutes:
            return False, f"Check-in too early. Shift starts at {sub_shift.time_start.strftime('%H:%M')}", minutes_early
        
        return True, "Check-in time is valid", minutes_early
        
    except Exception as e:
        return True, "Error validating check-in time", 0


def validate_check_out_time(sub_shift, check_out_time, check_in_time):
    """
    Validate check-out time and calculate early exit/overtime
    Returns: (is_valid, message, early_exit_minutes, overtime_minutes)
    """
    try:
        if not sub_shift or not sub_shift.time_end:
            return True, "No shift timing defined", 0, 0
        
        # Get current date
        current_date = timezone.localdate()
        
        # Convert times to datetime
        if isinstance(check_out_time, time):
            check_out_datetime = datetime.combine(current_date, check_out_time)
        else:
            check_out_datetime = check_out_time
        
        if isinstance(check_in_time, time):
            check_in_datetime = datetime.combine(current_date, check_in_time)
        else:
            check_in_datetime = check_in_time
        
        # Handle night shifts for check-out
        shift_start_time = sub_shift.time_start
        shift_end_time = sub_shift.time_end
        
        # For night shifts, check-out date might be the next day
        if shift_end_time and shift_start_time and shift_end_time < shift_start_time:
            # This is a night shift (e.g., 18:00 to 02:00)
            # For check-out, use the next day if check-out time is earlier than start time
            if check_out_datetime.time() < shift_start_time:
                # Check-out is on the next day
                shift_end = datetime.combine(current_date + timedelta(days=1), shift_end_time)
            else:
                # Check-out is on the same day
                shift_end = datetime.combine(current_date, shift_end_time)
        else:
            # Regular day shift
            shift_end = datetime.combine(current_date, sub_shift.time_end)
        
        # Calculate early exit and overtime
        early_exit_minutes = 0
        overtime_minutes = 0
        
        if check_out_datetime < shift_end:
            early_exit_minutes = int((shift_end - check_out_datetime).total_seconds() / 60)
        else:
            overtime_minutes = int((check_out_datetime - shift_end).total_seconds() / 60)
        
        # Calculate total worked time
        total_worked_minutes = int((check_out_datetime - check_in_datetime).total_seconds() / 60)
        
        # Validate minimum working hours (e.g., at least 4 hours)
        min_working_hours = 4 * 60  # 4 hours in minutes
        if total_worked_minutes < min_working_hours:
            return False, f"Minimum working hours not met. Worked: {total_worked_minutes//60}h {total_worked_minutes%60}m, Required: 4h", early_exit_minutes, overtime_minutes
        
        return True, "Check-out time is valid", early_exit_minutes, overtime_minutes
        
    except Exception as e:
        return True, "Error validating check-out time", 0, 0


def calculate_overtime_minutes(attendance, total_worked_minutes):
    """Calculate overtime minutes based on shift duration"""
    try:
        shift_minutes = 480  # Default 8 hours
        
        if attendance.sub_shift and attendance.sub_shift.time_end and attendance.sub_shift.time_start:
            # Get current date
            current_date = timezone.localdate()
            
            start_dt = datetime.combine(current_date, attendance.sub_shift.time_start)
            end_dt = datetime.combine(current_date, attendance.sub_shift.time_end)
            shift_minutes = max(0, int((end_dt - start_dt).total_seconds() / 60))
        
        return max(0, total_worked_minutes - shift_minutes)
    except Exception as e:
        # If any error occurs, return 0
        return 0


def calculate_break_duration(break_start_time, break_end_time, date):
    """Calculate break duration in minutes"""
    if isinstance(break_start_time, time):
        start_dt = datetime.combine(date, break_start_time)
    else:
        start_dt = break_start_time
    
    if isinstance(break_end_time, time):
        end_dt = datetime.combine(date, break_end_time)
    else:
        end_dt = break_end_time
    
    return int((end_dt - start_dt).total_seconds() / 60)


# Data validation utilities
def validate_employee_exists(employee_id):
    """Validate if employee exists"""
    # This would typically check against an Employee model
    # For now, we'll assume any positive integer is valid
    return employee_id > 0


def validate_attendance_type_exists(code):
    """Validate if attendance type exists"""
    try:
        attendance_type = AttendanceType.objects.get(code=code, deleted=False)
        return attendance_type
    except AttendanceType.DoesNotExist:
        # Try to create the attendance type if it doesn't exist
        try:
            if code == "P":
                attendance_type = AttendanceType.objects.create(
                    title="Present",
                    code="P",
                    color_code="#00FF00"
                )
            elif code == "A":
                attendance_type = AttendanceType.objects.create(
                    title="Absent",
                    code="A",
                    color_code="#FF0000"
                )
            elif code == "H":
                attendance_type = AttendanceType.objects.create(
                    title="Half Day",
                    code="H",
                    color_code="#FFFF00"
                )
            elif code == "WFH":
                attendance_type = AttendanceType.objects.create(
                    title="Work From Home",
                    code="WFH",
                    color_code="#0000FF"
                )
            else:
                return None
            return attendance_type
        except Exception:
            return None


# Response formatting utilities
def format_attendance_response(data, status="200"):
    """Format attendance response"""
    return {"data": data, "status": status}


def format_error_response(error_message, status="500"):
    """Format error response"""
    return {"error": error_message, "status": status}


def format_punch_response(message, action_type, action_id, time_field, time_value):
    """Format punch response"""
    return {
        "message": message,
        "action_type": action_type,
        "action_id": action_id,
        time_field: str(time_value)
    }


# Database utility functions
def get_or_create_attendance(employee_id, date, default_type):
    """Get or create attendance record with transaction safety"""
    try:
        # First try to get existing attendance for today
        try:
            attendance = Attendance.objects.get(
                employee=employee_id,
                date_check_in__date=date,
                deleted=False
            )
            return attendance, False
        except Attendance.DoesNotExist:
            # Create new attendance record
            attendance = Attendance.objects.create(
                employee=employee_id,
                attendance_type=default_type,
                company=1,  # Default company ID
                action_type='check_in'  # Default action type
            )
            return attendance, True
    except Exception as e:
        # If any error occurs, create a basic attendance record
        attendance = Attendance.objects.create(
            employee=employee_id,
            attendance_type=default_type,
            company=1,
            action_type='check_in'
        )
        return attendance, True


def get_employee_ids():
    """Get all employee IDs"""
    # This would typically query an Employee model
    # For now, return a list of test employee IDs
    return [1, 2, 3, 4, 5]


def get_active_shift_for_employee(employee_id, company_id=1):
    """
    Get the active shift and sub-shift for an employee
    Returns: (shift, sub_shift) tuple or (None, None) if not found
    """
    try:
        from shiftSetting.models import Shift, SubShift
        
        # First try to get the default/active shift for the company
        # For now, we'll get the first active shift available
        shift = Shift.objects.filter(
            company=company_id,
            deleted=False
        ).first()
        
        if not shift:
            return None, None
        
        # Get the active sub-shift for this shift
        sub_shift = SubShift.objects.filter(
            shift=shift,
            active=True,
            deleted=False
        ).first()
        
        return shift, sub_shift
        
    except Exception as e:
        # If any error occurs, return None values
        return None, None


def get_shift_by_time(employee_id, check_in_time, company_id=1):
    """
    Get the appropriate shift based on check-in time
    This can be used to assign different shifts based on time of day
    """
    try:
        from shiftSetting.models import Shift, SubShift
        from datetime import time
        
        # Get all available shifts for the company
        shifts = Shift.objects.filter(
            company=company_id,
            deleted=False
        )
        
        for shift in shifts:
            # Get sub-shifts for this shift
            sub_shifts = SubShift.objects.filter(
                shift=shift,
                active=True,
                deleted=False
            )
            
            for sub_shift in sub_shifts:
                if sub_shift.time_start and sub_shift.time_end:
                    # Check if check-in time falls within this sub-shift
                    if sub_shift.time_start <= check_in_time.time() <= sub_shift.time_end:
                        return shift, sub_shift
        
        # If no specific shift found, return the first available
        return get_active_shift_for_employee(employee_id, company_id)
        
    except Exception as e:
        # If any error occurs, return None values
        return None, None


def auto_mark_absent(date=None):
    """Auto mark absent for employees who haven't checked in"""
    if date is None:
        date = timezone.localdate()
    
    # Get all employee IDs
    employee_ids = get_employee_ids()
    
    # Get absent attendance type
    try:
        absent_type = AttendanceType.objects.get(code='A', deleted=False)
    except AttendanceType.DoesNotExist:
        return
    
    # Mark absent for employees who haven't checked in
    for employee_id in employee_ids:
        attendance_exists = Attendance.objects.filter(
            employee=employee_id,
            date_check_in__date=date,
            deleted=False
        ).exists()
        
        if not attendance_exists:
            Attendance.objects.create(
                employee=employee_id,
                attendance_type=absent_type,
                action_type='absent',
                date_check_in=timezone.make_aware(datetime.combine(date, datetime.min.time())),
                company=1
            )


def get_attendance_summary(employee_id, date):
    """Get attendance summary for employee on specific date"""
    try:
        attendance = Attendance.objects.get(
            employee=employee_id,
            date_check_in__date=date,
            deleted=False
        )
        
        summary = {
            "employee_id": employee_id,
            "date": date,
            "status": "checked_in" if attendance.date_check_in else "not_checked_in",
            "check_in_time": attendance.date_check_in.strftime("%H:%M:%S") if attendance.date_check_in else None,
            "check_out_time": attendance.date_check_out.strftime("%H:%M:%S") if attendance.date_check_out else None,
            "working_hours": attendance.working_hour if attendance.working_hour else 0,
            "is_late": attendance.is_late,
            "late_by_minutes": attendance.late_by_minutes if attendance.late_by_minutes else 0,
            "overtime_minutes": attendance.overtime_minutes if attendance.overtime_minutes else 0,
            "attendance_type": attendance.attendance_type.title if attendance.attendance_type else "Unknown",
            "action_type": attendance.action_type
        }
        
        return summary
        
    except Attendance.DoesNotExist:
        return {
            "employee_id": employee_id,
            "date": date,
            "status": "not_checked_in",
            "check_in_time": None,
            "check_out_time": None,
            "working_hours": 0,
            "is_late": False,
            "late_by_minutes": 0,
            "overtime_minutes": 0,
            "attendance_type": "Unknown",
            "action_type": None
        }


def get_employee_attendance_status(employee_id):
    """Get employee's current attendance status for today"""
    try:
        today = timezone.localdate()
        
        # Get today's attendance record
        attendance = Attendance.objects.filter(
            employee=employee_id,
            date_check_in__date=today,
            deleted=False
        ).first()
        
        if not attendance:
            return {
                "employee": employee_id,
                "status": "not_checked_in",
                "message": "Employee not checked in today"
            }
        
        # Check if checked out
        if attendance.date_check_out:
            return {
                "employee": employee_id,
                "status": "checked_out",
                "check_in_time": attendance.date_check_in,
                "check_out_time": attendance.date_check_out,
                "working_hours": attendance.working_hour,
                "message": "Employee checked out for the day"
            }
        else:
            return {
                "employee": employee_id,
                "status": "checked_in",
                "check_in_time": attendance.date_check_in,
                "message": "Employee is currently checked in"
            }
            
    except Exception as e:
        return format_error_response(f"Error getting employee status: {str(e)}")


def validate_attendance_punch(employee_id, action_type):
    """Validate attendance punch request"""
    try:
        today = timezone.localdate()
        
        if action_type == "check_in":
            # Check if already checked in today
            existing_attendance = Attendance.objects.filter(
                employee=employee_id,
                date_check_in__date=today,
                deleted=False
            ).first()
            
            if existing_attendance:
                return False, "Employee is already checked in today"
            
            return True, "Valid check-in request"
        
        elif action_type == "check_out":
            # Check if checked in today
            attendance = Attendance.objects.filter(
                employee=employee_id,
                date_check_in__date=today,
                date_check_out__isnull=True,
                deleted=False
            ).first()
            
            if not attendance:
                return False, "No check-in record found for today"
            
            if attendance.date_check_out:
                return False, "Employee is already checked out for today"
            
            return True, "Valid check-out request"
        
        else:
            return False, "Invalid action type. Only 'check_in' and 'check_out' are supported"
            
    except Exception as e:
        return False, f"Error validating attendance punch: {str(e)}"


# Legacy functions for backward compatibility
def get_open_punch(attendance):
    """Legacy function - now returns None as we don't use punches"""
    return None


def check_duplicate_punch(attendance, action_code):
    """Legacy function - check if action already exists for today"""
    today = timezone.localdate()
    return Attendance.objects.filter(
        employee=attendance.employee,
        action_type=action_code,
        date_check_in__date=today,
        deleted=False
    ).exists()


def create_attendance_punch(employee_id, date, attendance, action, check_in_time):
    """Legacy function - now creates attendance record directly"""
    return Attendance.objects.create(
        employee=employee_id,
        action_type=action,
        date_check_in=check_in_time,
        attendance_type=attendance.attendance_type,
        company=attendance.company
    ) 