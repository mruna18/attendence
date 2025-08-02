from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import *
from .utils import *


# Business Logic Services
class AttendanceService:
    """Service class for attendance business logic"""
    
    @staticmethod
    def process_check_in(employee_id, action, today, now_time, present_type):
        """Process check-in business logic"""
        attendance, _ = get_or_create_attendance(employee_id, today, present_type)
        
        # Check if already checked in
        if get_open_punch(attendance):
            return format_error_response("Already checked in. Please check out first.")
        
        # Create punch
        punch = create_attendance_punch(employee_id, today, attendance, action, now_time)
        
        # Update attendance record
        attendance.check_in_time = now_time
        if not attendance.attendance_type:
            attendance.attendance_type = present_type
        
        # Calculate late minutes
        attendance.late_by_minutes = calculate_late_minutes(attendance, now_time)
        attendance.save()
        
        return format_punch_response(
            "Check-in successful",
            action.name,
            action.id,
            "check_in_time",
            punch.check_in_time
        )
    
    @staticmethod
    def process_check_out(employee_id, action, today, now_time, present_type):
        """Process check-out business logic"""
        try:
            attendance = Attendance.objects.select_for_update().get(
                employee=employee_id, date=today, is_deleted=False
            )
        except Attendance.DoesNotExist:
            return format_error_response("No attendance found for today")
        
        open_punch = get_open_punch(attendance)
        if not open_punch:
            return format_error_response("No open check-in found for today")
        
        # Close the punch
        open_punch.check_out_time = now_time
        open_punch.save()
        
        # Update attendance record
        attendance.check_out_time = now_time
        if not attendance.attendance_type:
            attendance.attendance_type = present_type
        
        # Calculate worked and overtime minutes
        total_minutes = calculate_worked_minutes(attendance)
        attendance.overtime_minutes = calculate_overtime_minutes(attendance, total_minutes)
        attendance.save()
        
        return format_attendance_response({
            "message": "Check-out successful",
            "action": action.name,
            "action_id": action.id,
            "check_out_time": str(open_punch.check_out_time),
            "worked_minutes_today": total_minutes,
            "overtime_minutes": attendance.overtime_minutes
        })
    
    @staticmethod
    def process_break_start(employee_id, action, today, now_time):
        """Process break start business logic"""
        try:
            attendance = Attendance.objects.select_for_update().get(
                employee=employee_id, date=today, is_deleted=False
            )
        except Attendance.DoesNotExist:
            return format_error_response("No attendance found for today")
        
        # Check if already on break
        if check_duplicate_punch(attendance, action.code):
            return format_error_response(f"Already on {action.name.lower()}")
        
        # Create break punch
        punch = create_attendance_punch(employee_id, today, attendance, action, now_time)
        
        return format_punch_response(
            f"{action.name} started",
            action.name,
            action.id,
            "break_start_time",
            punch.check_in_time
        )
    
    @staticmethod
    def process_break_end(employee_id, action, today, now_time):
        """Process break end business logic"""
        try:
            attendance = Attendance.objects.select_for_update().get(
                employee=employee_id, date=today, is_deleted=False
            )
        except Attendance.DoesNotExist:
            return format_error_response("No attendance found for today")
        
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
            return format_error_response(f"No open {action.name.lower()} found")
        
        # Close the break
        open_break.check_out_time = now_time
        open_break.save()
        
        # Calculate break duration
        break_duration = calculate_break_duration(
            open_break.check_in_time, now_time, today
        )
        
        return format_attendance_response({
            "message": f"{action.name} ended",
            "action": action.name,
            "action_id": action.id,
            "break_end_time": str(now_time),
            "break_duration_minutes": break_duration
        })
    
    @staticmethod
    def process_half_day(employee_id, action, today, now_time, present_type):
        """Process half-day business logic"""
        attendance, _ = get_or_create_attendance(employee_id, today, present_type)
        
        # Create half day punch
        punch = create_attendance_punch(employee_id, today, attendance, action, now_time)
        
        # Set attendance type to half day
        half_day_type = validate_attendance_type_exists("H")
        if half_day_type:
            attendance.attendance_type = half_day_type
        
        attendance.save()
        
        return format_punch_response(
            "Half day marked successfully",
            action.name,
            action.id,
            "half_day_time",
            punch.check_in_time
        )
    
    @staticmethod
    def process_work_from_home(employee_id, action, today, now_time, present_type):
        """Process work from home business logic"""
        attendance, _ = get_or_create_attendance(employee_id, today, present_type)
        
        # Create WFH punch
        punch = create_attendance_punch(employee_id, today, attendance, action, now_time)
        
        # Set attendance type to WFH
        wfh_type = validate_attendance_type_exists("WFH")
        if wfh_type:
            attendance.attendance_type = wfh_type
        
        attendance.save()
        
        return format_punch_response(
            "Work from home marked successfully",
            action.name,
            action.id,
            "wfh_time",
            punch.check_in_time
        )
    
    @staticmethod
    def process_generic_action(employee_id, action, today, now_time):
        """Process generic action business logic"""
        try:
            attendance = Attendance.objects.select_for_update().get(
                employee=employee_id, date=today, is_deleted=False
            )
        except Attendance.DoesNotExist:
            return format_error_response("No attendance found for today")
        
        punch = create_attendance_punch(employee_id, today, attendance, action, now_time)
        
        return format_punch_response(
            f"{action.name} successful",
            action.name,
            action.id,
            "action_time",
            punch.check_in_time
        )


class AttendanceReportService:
    """Service class for attendance reporting"""
    
    @staticmethod
    def get_employee_attendance_summary(employee_id, date):
        """Get attendance summary for employee"""
        return get_attendance_summary(employee_id, date)
    
    @staticmethod
    def get_attendance_report(employee_id=None, start_date=None, end_date=None):
        """Generate attendance report"""
        queryset = Attendance.objects.filter(is_deleted=False)
        
        if employee_id:
            queryset = queryset.filter(employee=employee_id)
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')
    
    @staticmethod
    def auto_mark_absent_service():
        """Auto-mark absent service"""
        auto_mark_absent()


# Legacy functions (kept for backward compatibility)
def get_all_employee_ids():
    """Get all employee IDs (legacy function)"""
    return get_employee_ids()


def calculate_worked_minutes_legacy(attendance):
    """Calculate worked minutes (legacy function)"""
    return calculate_worked_minutes(attendance)


def auto_mark_absent_legacy():
    """Auto-mark absent (legacy function)"""
    auto_mark_absent()
