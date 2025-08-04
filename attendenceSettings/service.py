from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import *
from .utils import *


# Business Logic Services
class AttendanceService:
    """Service class for attendance business logic"""
    
    @staticmethod
    def process_check_in(employee_id, action_type, today, now_time, present_type, source_id=None, remarks=""):
        """Process check-in business logic"""
        try:
            # Step 1: Get or create attendance
            attendance, created = get_or_create_attendance(employee_id, today, present_type)
            
            # Step 2: Check if already checked in
            if attendance.date_check_in:
                return format_error_response("Already checked in. Please check out first.")
            
            # Step 3: Fetch and assign active shift based on check-in time
            try:
                shift, sub_shift = get_shift_by_time(employee_id, now_time)
                if shift:
                    attendance.shift = shift
                if sub_shift:
                    attendance.sub_shift = sub_shift
            except Exception as shift_error:
                # If shift assignment fails, continue without shift
                pass
            
            # Step 4: Update attendance record
            attendance.action_type = action_type
            attendance.date_check_in = now_time
            if not attendance.attendance_type:
                attendance.attendance_type = present_type
            
            # Step 4.1: Assign source and remarks if provided
            if source_id:
                try:
                    source = Source.objects.get(id=source_id, deleted=False)
                    attendance.source = source
                except Source.DoesNotExist:
                    # If source not found, continue without source
                    pass
            
            if remarks:
                attendance.remarks = remarks
            
            # Step 5: Calculate late minutes (with error handling)
            try:
                attendance.late_by_minutes = calculate_late_minutes(attendance, now_time)
            except Exception as late_error:
                # If late calculation fails, set to 0 and continue
                attendance.late_by_minutes = 0
            
            # Step 6: Save attendance
            attendance.save()
            
            return format_punch_response(
                "Check-in successful",
                action_type,
                action_type,
                "date_check_in",
                attendance.date_check_in
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return format_error_response(f"Error during check-in: {str(e)}\nDetails: {error_details}")
    
    @staticmethod
    def process_check_out(employee_id, action_type, today, now_time, present_type, source_id=None, remarks=""):
        # """Process check-out business logic"""
        # from datetime import datetime, time

        try:
            # Step 1: Define start and end of day
            start_of_day = datetime.combine(today, time.min)
            end_of_day = datetime.combine(today, time.max)

            # Step 2: Get existing attendance (handle multiple records)
            try:
                # Get the most recent attendance record for today that hasn't been checked out
                attendance = Attendance.objects.filter(
                    employee=employee_id,
                    date_check_in__range=(start_of_day, end_of_day),
                    date_check_out__isnull=True,  # Only get records that haven't been checked out
                    deleted=False
                ).order_by('-date_check_in').first()  # Get the most recent one
                
                if not attendance:
                    return format_error_response("No active attendance found for today")
            except Exception as e:
                return format_error_response(f"Error finding attendance: {str(e)}")

            # Step 3: Validate check-in exists
            if not attendance.date_check_in:
                return format_error_response("No check-in found for today")

            # Step 4: Check if already checked out
            if attendance.date_check_out:
                return format_error_response("Already checked out for today")

            # Step 5: Update attendance record
            attendance.action_type = action_type
            attendance.date_check_out = now_time
            if not attendance.attendance_type:
                attendance.attendance_type = present_type
            
            # Step 5.1: Assign source and remarks if provided
            if source_id:
                try:
                    source = Source.objects.get(id=source_id, deleted=False)
                    attendance.source = source
                except Source.DoesNotExist:
                    # If source not found, continue without source
                    pass
            
            if remarks:
                attendance.remarks = remarks
            
            # Step 5.1: Ensure shift is assigned (if not already assigned)
            if not attendance.shift or not attendance.sub_shift:
                try:
                    shift, sub_shift = get_active_shift_for_employee(employee_id)
                    if shift and not attendance.shift:
                        attendance.shift = shift
                    if sub_shift and not attendance.sub_shift:
                        attendance.sub_shift = sub_shift
                except Exception as shift_error:
                    # If shift assignment fails, continue without shift
                    pass

            # Step 6: Calculate worked hours and overtime
            try:
                if attendance.date_check_in and attendance.date_check_out:
                    time_diff = attendance.date_check_out - attendance.date_check_in
                    attendance.working_hour = int(time_diff.total_seconds() //  60)# Convert to hours
                    attendance.overtime_minutes = calculate_overtime_minutes(attendance, attendance.working_hour * 60)
            except Exception:
                attendance.working_hour = 0
                attendance.overtime_minutes = 0

            # Step 7: Save attendance
            attendance.save()

            return format_punch_response(
                "Check-out successful",
                action_type,
                action_type,
                "date_check_out",
                attendance.date_check_out
            )
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return format_error_response(f"Error during check-out: {str(e)}\nDetails: {error_details}")

    
    @staticmethod
    def process_break_start(employee_id, action_type, today, now_time, source_id=None, remarks=""):
        """Process break start business logic"""
        try:
            # Get the most recent attendance record for today
            attendance = Attendance.objects.filter(
                employee=employee_id, 
                date_check_in__date=today, 
                deleted=False
            ).order_by('-date_check_in').first()
            
            if not attendance:
                return format_error_response("No attendance found for today")
        except Exception as e:
            return format_error_response(f"Error finding attendance: {str(e)}")
        
        # Check if already on break
        existing_break = Attendance.objects.filter(
            employee=employee_id,
            action_type=action_type,
            date_check_in__date=today,
            date_check_out__isnull=True,
            deleted=False
        ).exists()
        
        if existing_break:
            return format_error_response(f"Already on {action_type.replace('_', ' ')}")
        
        # Create break record
        break_data = {
            'employee': employee_id,
            'action_type': action_type,
            'date_check_in': now_time,
            'attendance_type': attendance.attendance_type
        }
        
        # Add source if provided
        if source_id:
            try:
                source = Source.objects.get(id=source_id, deleted=False)
                break_data['source'] = source
            except Source.DoesNotExist:
                # If source not found, continue without source
                pass
        
        # Add remarks if provided
        if remarks:
            break_data['remarks'] = remarks
        
        break_attendance = Attendance.objects.create(**break_data)
        
        return format_punch_response(
            f"{action_type.replace('_', ' ').title()} started",
            action_type,
            action_type,
            "break_start_time",
            break_attendance.date_check_in
        )
    
    @staticmethod
    def process_break_end(employee_id, action_type, today, now_time, source_id=None, remarks=""):
        """Process break end business logic"""
        # Find open break
        if action_type == "break_end":
            open_break = Attendance.objects.filter(
                employee=employee_id,
                action_type="break_start",
                date_check_in__date=today,
                date_check_out__isnull=True,
                deleted=False
            ).last()
        else:  # lunch_end
            open_break = Attendance.objects.filter(
                employee=employee_id,
                action_type="lunch_start",
                date_check_in__date=today,
                date_check_out__isnull=True,
                deleted=False
            ).last()
        
        if not open_break:
            return format_error_response(f"No open {action_type.replace('_', ' ')} found")
        
        # Close the break
        open_break.date_check_out = now_time
        open_break.save()
        
        # Calculate break duration
        break_duration = calculate_break_duration(
            open_break.date_check_in, now_time, today
        )
        
        return {
            "message": f"{action_type.replace('_', ' ').title()} ended",
            "action_type": action_type,
            "break_end_time": str(now_time),
            "break_duration_minutes": break_duration
        }
    
    @staticmethod
    def process_half_day(employee_id, action_type, today, now_time, present_type, source_id=None, remarks=""):
        """Process half-day business logic"""
        attendance, _ = get_or_create_attendance(employee_id, today, present_type)
        
        # Update attendance record
        attendance.action_type = action_type
        attendance.date_check_in = now_time
        
        # Set attendance type to half day
        half_day_type = validate_attendance_type_exists("H")
        if half_day_type:
            attendance.attendance_type = half_day_type
        
        # Assign source and remarks if provided
        if source_id:
            try:
                source = Source.objects.get(id=source_id, deleted=False)
                attendance.source = source
            except Source.DoesNotExist:
                # If source not found, continue without source
                pass
        
        if remarks:
            attendance.remarks = remarks
        
        attendance.save()
        
        return format_punch_response(
            "Half day marked successfully",
            action_type,
            action_type,
            "half_day_time",
            attendance.date_check_in
        )
    
    @staticmethod
    def process_work_from_home(employee_id, action_type, today, now_time, present_type, source_id=None, remarks=""):
        """Process work from home business logic"""
        attendance, _ = get_or_create_attendance(employee_id, today, present_type)
        
        # Update attendance record
        attendance.action_type = action_type
        attendance.date_check_in = now_time
        
        # Set attendance type to WFH
        wfh_type = validate_attendance_type_exists("WFH")
        if wfh_type:
            attendance.attendance_type = wfh_type
        
        # Assign source and remarks if provided
        if source_id:
            try:
                source = Source.objects.get(id=source_id, deleted=False)
                attendance.source = source
            except Source.DoesNotExist:
                # If source not found, continue without source
                pass
        
        if remarks:
            attendance.remarks = remarks
        
        attendance.save()
        
        return format_punch_response(
            "Work from home marked successfully",
            action_type,
            action_type,
            "wfh_time",
            attendance.date_check_in
        )
    
    @staticmethod
    def process_generic_action(employee_id, action_type, today, now_time, source_id=None, remarks=""):
        """Process generic action business logic"""
        try:
            attendance = Attendance.objects.get(
                employee=employee_id, 
                date_check_in__date=today, 
                deleted=False
            )
        except Attendance.DoesNotExist:
            return format_error_response("No attendance found for today")
        
        # Create generic action record
        generic_data = {
            'employee': employee_id,
            'action_type': action_type,
            'date_check_in': now_time,
            'attendance_type': attendance.attendance_type
        }
        
        # Add source if provided
        if source_id:
            try:
                source = Source.objects.get(id=source_id, deleted=False)
                generic_data['source'] = source
            except Source.DoesNotExist:
                # If source not found, continue without source
                pass
        
        # Add remarks if provided
        if remarks:
            generic_data['remarks'] = remarks
        
        generic_attendance = Attendance.objects.create(**generic_data)
        
        return format_punch_response(
            f"{action_type.replace('_', ' ').title()} successful",
            action_type,
            action_type,
            "action_time",
            generic_attendance.date_check_in
        )


class LeaveService:
    """Service class for leave business logic"""
    
    @staticmethod
    def create_leave_request(data):
        """Create a new leave request"""
        try:
            attendance_type = AttendanceType.objects.get(id=data['attendance_type'].id, is_leave=True, deleted=False)
        except AttendanceType.DoesNotExist:
            raise Exception("Selected attendance type is not a valid leave type.")
        
        # Get pending status
        try:
            pending_status = Status.objects.get(code='pending', is_active=True, deleted=False)
        except Status.DoesNotExist:
            raise Exception("Pending status not found")
        
        # Check leave balance
        balance_check = LeaveService.check_leave_balance(
            data['employee'], 
            data['attendance_type'].id, 
            data['start_date'], 
            data['end_date']
        )
        if not balance_check["has_sufficient_balance"]:
            raise Exception(f"Insufficient leave balance. {balance_check['message']}")
        
        # Create leave request
        leave_request = LeaveRequest.objects.create(
            employee=data['employee'],
            attendance_type=attendance_type,
            start_date=data['start_date'],
            end_date=data['end_date'],
            reason=data.get('reason', ''),
            status=pending_status
        )
        
        return {
            "message": "Leave request created successfully",
            "leave_request_id": leave_request.id,
            "total_days": leave_request.total_days,
            "status": leave_request.status.label
        }
    
    @staticmethod
    def approve_leave_request(leave_request_id, approver_id, approval_remarks=""):
        """Approve a leave request"""
        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id, deleted=False)
        except LeaveRequest.DoesNotExist:
            raise Exception("Leave request not found")
        
        if leave_request.status.code != 'pending':
            raise Exception(f"Leave request is already {leave_request.status.label}")
        
        # Get approved status
        try:
            approved_status = Status.objects.get(code='approved', is_active=True, deleted=False)
        except Status.DoesNotExist:
            raise Exception("Approved status not found")
        
        # Update leave request
        leave_request.status = approved_status
        leave_request.approved_by = approver_id
        leave_request.approved_at = timezone.now()
        leave_request.approval_remarks = approval_remarks
        leave_request.save()
        
        # Update leave balance
        LeaveService.update_leave_balance(leave_request.employee, leave_request.attendance_type.id, leave_request.total_days)
        
        return {
            "message": "Leave request approved successfully",
            "leave_request_id": leave_request.id,
            "approved_by": approver_id,
            "approved_at": str(leave_request.approved_at)
        }
    
    @staticmethod
    def reject_leave_request(leave_request_id, approver_id, approval_remarks=""):
        """Reject a leave request"""
        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id, deleted=False)
        except LeaveRequest.DoesNotExist:
            raise Exception("Leave request not found")
        
        if leave_request.status.code != 'pending':
            raise Exception(f"Leave request is already {leave_request.status.label}")
        
        # Get rejected status
        try:
            rejected_status = Status.objects.get(code='rejected', is_active=True, deleted=False)
        except Status.DoesNotExist:
            raise Exception("Rejected status not found")
        
        # Update leave request
        leave_request.status = rejected_status
        leave_request.approved_by = approver_id
        leave_request.approved_at = timezone.now()
        leave_request.approval_remarks = approval_remarks
        leave_request.save()
        
        return {
            "message": "Leave request rejected successfully",
            "leave_request_id": leave_request.id,
            "rejected_by": approver_id,
            "rejected_at": str(leave_request.approved_at)
        }
    
    @staticmethod
    def cancel_leave_request(leave_request_id):
        """Cancel a leave request"""
        try:
            leave_request = LeaveRequest.objects.get(id=leave_request_id, deleted=False)
        except LeaveRequest.DoesNotExist:
            raise Exception("Leave request not found")
        
        # Check if already cancelled
        if leave_request.status.code == 'cancelled':
            raise Exception("Leave request is already cancelled")
        
        # Get cancelled status
        try:
            cancelled_status = Status.objects.get(code='cancelled', is_active=True, deleted=False)
        except Status.DoesNotExist:
            raise Exception("Cancelled status not found")
        
        # If the leave was approved, we need to restore the leave balance
        if leave_request.status.code == 'approved':
            # Restore the leave balance by subtracting the used days
            LeaveService.update_leave_balance(
                leave_request.employee, 
                leave_request.attendance_type.id, 
                -leave_request.total_days  # Negative to restore balance
            )
        
        # Update leave request
        leave_request.status = cancelled_status
        leave_request.save()
        
        return {
            "message": "Leave request cancelled successfully",
            "leave_request_id": leave_request.id,
            "previous_status": leave_request.status.label,
            "balance_restored": leave_request.status.code == 'approved'
        }
    
    @staticmethod
    def check_leave_balance(employee_id, attendance_type_id, start_date, end_date):
        """Check if employee has sufficient leave balance"""
        try:
            attendance_type = AttendanceType.objects.get(id=attendance_type_id, deleted=False)
        except AttendanceType.DoesNotExist:
            return {"has_sufficient_balance": False, "message": "Attendance type not found"}
        
        # Calculate required days
        delta = end_date - start_date
        required_days = delta.days + 1
        
        # Get current year
        current_year = timezone.now().year
        
        # Get or create leave balance
        leave_balance, created = LeaveBalance.objects.get_or_create(
            employee=employee_id,
            leave_type=attendance_type,
            year=current_year,
            defaults={'total_days': 0, 'used_days': 0, 'remaining_days': 0}
        )
        
        # If this is a LOP (Loss of Pay) type, always allow
        if hasattr(attendance_type, 'is_lop') and attendance_type.is_lop:
            return {
                "has_sufficient_balance": True,
                "message": f"LOP leave - {required_days} days requested"
            }
        
        # If no balance is set up yet, provide helpful message
        if leave_balance.total_days == 0:
            return {
                "has_sufficient_balance": False,
                "message": f"No leave balance set up for {attendance_type.title}. Please contact HR to set up leave allocation."
            }
        
        if leave_balance.remaining_days < required_days:
            return {
                "has_sufficient_balance": False,
                "message": f"Required: {required_days} days, Available: {leave_balance.remaining_days} days for {attendance_type.title}"
            }
        
        return {
            "has_sufficient_balance": True,
            "message": f"Available: {leave_balance.remaining_days} days for {attendance_type.title}"
        }
    
    @staticmethod
    def update_leave_balance(employee_id, attendance_type_id, used_days, year=None):
        """Update leave balance after approval"""
        if year is None:
            year = timezone.now().year
        
        try:
            leave_balance = LeaveBalance.objects.get(
                employee=employee_id,
                leave_type_id=attendance_type_id,
                year=year,
                deleted=False
            )
            leave_balance.used_days += used_days
            leave_balance.save()
        except LeaveBalance.DoesNotExist:
            # Create new balance record if doesn't exist
            attendance_type = AttendanceType.objects.get(id=attendance_type_id)
            LeaveBalance.objects.create(
                employee=employee_id,
                leave_type=attendance_type,
                year=year,
                total_days=0,
                used_days=used_days
            )
    
    @staticmethod
    def get_employee_leave_balance(employee_id, year=None):
        """Get employee's leave balance for all leave types"""
        if year is None:
            year = timezone.now().year
        
        balances = LeaveBalance.objects.filter(
            employee=employee_id,
            year=year,
            deleted=False
        ).select_related('leave_type')
        
        return balances


class AttendanceReportService:
    """Service class for attendance reporting"""
    
    @staticmethod
    def get_employee_attendance_summary(employee_id, date):
        """Get attendance summary for employee"""
        return get_attendance_summary(employee_id, date)
    
    @staticmethod
    def get_employee_status(employee_id, date):
        """Get current employee status (checked in/out)"""
        if not employee_id:
            return format_error_response("employee parameter is required")
        
        result = get_attendance_summary(employee_id, date)
        return result
    
    @staticmethod
    def get_attendance_list(employee_id=None):
        """Get attendance list with optional employee filtering"""
        queryset = Attendance.objects.filter(deleted=False)
        if employee_id:
            queryset = queryset.filter(employee=employee_id)
        return queryset.order_by('-date_check_in')
    
    @staticmethod
    def get_attendance_report(employee_id=None, start_date=None, end_date=None):
        """Generate attendance report"""
        queryset = Attendance.objects.filter(deleted=False)
        
        if employee_id:
            queryset = queryset.filter(employee=employee_id)
        
        if start_date:
            queryset = queryset.filter(date_check_in__date__gte=start_date)
        
        if end_date:
            queryset = queryset.filter(date_check_in__date__lte=end_date)
        
        return queryset.order_by('-date_check_in')
    
    @staticmethod
    def auto_mark_absent_service(date=None):
        """Auto-mark absent service"""
        if date is None:
            date = timezone.localdate()
        auto_mark_absent(date)


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


def get_lop_days(employee_id, start_date, end_date):
    """Get LOP days for employee in date range"""
    lop_type = AttendanceType.objects.get(code='A')  # Or LOP type code
    return Attendance.objects.filter(
        employee=employee_id,
        attendance_type=lop_type,
        date_check_in__date__range=(start_date, end_date),
        deleted=False
    ).count()


def calculate_lop_deduction(gross_salary, month_days, lop_days):
    """Calculate LOP deduction from salary"""
    return (gross_salary / month_days) * lop_days
