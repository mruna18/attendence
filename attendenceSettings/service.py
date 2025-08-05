from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from .models import Action, AttendanceType, Source, Attendance


# Business Logic Services
class AttendanceService:
    """Service class for attendance business logic - Check In and Check Out only"""
    
    @staticmethod
    @transaction.atomic
    def process_attendance_punch(employee_id, action_type_id, source_id=None, remarks="", custom_timestamp=None):
        """Simplified attendance punch service for check-in and check-out only with shift integration"""
        try:
            # Use custom timestamp if provided, otherwise use current time
            if custom_timestamp:
                now_time = custom_timestamp
                today = now_time.date()
            else:
                today = timezone.localdate()
                now_time = timezone.localtime()
            
            # Get attendance types
            try:
                present_type = AttendanceType.objects.get(code="P", deleted=False)
                late_type = AttendanceType.objects.get(code="L", deleted=False)
            except AttendanceType.DoesNotExist:
                return {"error": "Required attendance types (P or L) not found", "status": "400"}
            
            # Get Action object by ID
            try:
                action = Action.objects.get(id=action_type_id, deleted=False)
            except Action.DoesNotExist:
                return {"error": f"Action with ID {action_type_id} not found", "status": "400"}
            
            # Get source if provided
            source = None
            if source_id:
                try:
                    source = Source.objects.get(id=source_id, deleted=False)
                except Source.DoesNotExist:
                    return {"error": f"Source with ID {source_id} not found", "status": "400"}
            
            # Process check-in
            if action.code == "check_in":
                # Check if employee is already checked in today
                existing_attendance = Attendance.objects.filter(
                    employee=employee_id,
                    date_check_in__date=today,
                    deleted=False
                ).first()
                
                if existing_attendance:
                    return {"error": "Employee is already checked in today", "status": "400"}
                
                # Get employee's shift and sub-shift
                from .utils import get_shift_by_time, validate_check_in_time
                shift, sub_shift = get_shift_by_time(employee_id, now_time)
                
                # Validate check-in time against shift
                is_valid_check_in = True
                check_in_message = ""
                minutes_early = 0
                
                if shift and sub_shift:
                    is_valid_check_in, check_in_message, minutes_early = validate_check_in_time(
                        sub_shift, now_time, allow_early_check_in=True, early_buffer_minutes=30
                    )
                    
                    if not is_valid_check_in:
                        return {"error": check_in_message, "status": "400"}
                
                # Calculate late minutes if shift exists
                late_minutes = 0
                is_late = False
                if shift and sub_shift:
                    from .utils import calculate_late_minutes
                    late_minutes = calculate_late_minutes(
                        type('obj', (object,), {'sub_shift': sub_shift})(), 
                        now_time,
                        grace_period_minutes=15
                    )
                    is_late = late_minutes > 0
                    
                    
                
                # Determine attendance type based on late status
                attendance_type = late_type if is_late else present_type
                
                # Create check-in record
                try:
                    attendance = Attendance.objects.create(
                        employee=employee_id,
                        attendance_type=attendance_type,
                        action=action,
                        date_check_in=now_time,
                        source=source,
                        remarks=remarks,
                        shift=shift,
                        sub_shift=sub_shift,
                        is_late=is_late,
                        late_by_minutes=late_minutes if is_late else None,
                        deleted=False
                    )
                except Exception as create_error:
                    return {"error": f"Error creating attendance record: {str(create_error)}", "status": "400"}
                
                response_data = {
                    "message": "Check-in successful",
                    "employee": employee_id,
                    "check_in_time": now_time,
                    "attendance_id": attendance.id,
                    "status": "checked_in",
                    "attendance_type": {
                        "id": attendance_type.id,
                        "code": attendance_type.code,
                        "title": attendance_type.title
                    }
                }
                
                # Add remarks if provided
                if remarks:
                    response_data["remarks"] = remarks
                
                # Add shift information to response
                if shift:
                    response_data["shift"] = {
                        "id": shift.id,
                        "name": shift.shift_head,
                        "description": shift.description
                    }
                if sub_shift:
                    response_data["sub_shift"] = {
                        "id": sub_shift.id,
                        "title": sub_shift.title,
                        "time_start": sub_shift.time_start.strftime("%H:%M") if sub_shift.time_start else None,
                        "time_end": sub_shift.time_end.strftime("%H:%M") if sub_shift.time_end else None
                    }
                if is_late:
                    response_data["late_minutes"] = late_minutes
                    response_data["is_late"] = True
                elif minutes_early > 0:
                    response_data["minutes_early"] = minutes_early
                    response_data["is_early_check_in"] = True
                
                return response_data
            
            # Process check-out
            elif action.code == "check_out":
                # Find today's check-in record
                attendance = Attendance.objects.filter(
                    employee=employee_id,
                    date_check_in__date=today,
                    date_check_out__isnull=True,
                    deleted=False
                ).first()
                
                if not attendance:
                    return {"error": "No check-in record found for today", "status": "400"}
                
                # Validate check-out time against shift
                is_valid_check_out = True
                check_out_message = ""
                early_exit_minutes = 0
                overtime_minutes = 0
                
                if attendance.sub_shift:
                    from .utils import validate_check_out_time
                    is_valid_check_out, check_out_message, early_exit_minutes, overtime_minutes = validate_check_out_time(
                        attendance.sub_shift, now_time, attendance.date_check_in
                    )
                    
                    if not is_valid_check_out:
                        return {"error": check_out_message, "status": "400"}
                
                # Update check-out time
                try:
                    attendance.date_check_out = now_time
                    
                    # Calculate working hours
                    if attendance.date_check_in:
                        time_diff = now_time - attendance.date_check_in
                        working_hours = time_diff.total_seconds() / 3600  # Convert to hours
                        attendance.working_hour = round(working_hours, 2)
                    
                    # Set overtime minutes
                    attendance.overtime_minutes = overtime_minutes
                    
                    attendance.save()
                except Exception as save_error:
                    return {"error": f"Error updating attendance record: {str(save_error)}", "status": "400"}
                
                response_data = {
                    "message": "Check-out successful",
                    "employee": employee_id,
                    "check_in_time": attendance.date_check_in,
                    "check_out_time": now_time,
                    "working_hours": attendance.working_hour,
                    "attendance_id": attendance.id,
                    "status": "checked_out",
                    "attendance_type": {
                        "id": attendance.attendance_type.id,
                        "code": attendance.attendance_type.code,
                        "title": attendance.attendance_type.title
                    }
                }
                
                # Add remarks if available
                if attendance.remarks:
                    response_data["remarks"] = attendance.remarks
                
                # Add shift information to response
                if attendance.shift:
                    response_data["shift"] = {
                        "id": attendance.shift.id,
                        "name": attendance.shift.shift_head,
                        "description": attendance.shift.description
                    }
                if attendance.sub_shift:
                    response_data["sub_shift"] = {
                        "id": attendance.sub_shift.id,
                        "title": attendance.sub_shift.title,
                        "time_start": attendance.sub_shift.time_start.strftime("%H:%M") if attendance.sub_shift.time_start else None,
                        "time_end": attendance.sub_shift.time_end.strftime("%H:%M") if attendance.sub_shift.time_end else None
                    }
                if attendance.is_late:
                    response_data["late_minutes"] = attendance.late_by_minutes
                    response_data["is_late"] = True
                if early_exit_minutes > 0:
                    response_data["early_exit_minutes"] = early_exit_minutes
                    response_data["early_exit_hours"] = round(early_exit_minutes / 60, 2)
                    response_data["is_early_exit"] = True
                if overtime_minutes > 0:
                    response_data["overtime_minutes"] = overtime_minutes
                    response_data["overtime_hours"] = round(overtime_minutes / 60, 2)
                    response_data["is_overtime"] = True
                
                return response_data
            
            else:
                return {"error": "Invalid action type. Only check_in and check_out actions are supported", "status": "400"}
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return {"error": f"Error processing attendance punch: {str(e)}", "details": error_details, "status": "500"}
    
    @staticmethod
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
            
            # Base response data
            response_data = {
                "employee": employee_id,
                "check_in_time": attendance.date_check_in,
                "attendance_type": {
                    "id": attendance.attendance_type.id,
                    "code": attendance.attendance_type.code,
                    "title": attendance.attendance_type.title
                }
            }
            
            # Add remarks if available
            if attendance.remarks:
                response_data["remarks"] = attendance.remarks
            
            # Add shift information if available
            if attendance.shift:
                response_data["shift"] = {
                    "id": attendance.shift.id,
                    "name": attendance.shift.shift_head,
                    "description": attendance.shift.description
                }
            if attendance.sub_shift:
                response_data["sub_shift"] = {
                    "id": attendance.sub_shift.id,
                    "title": attendance.sub_shift.title,
                    "time_start": attendance.sub_shift.time_start.strftime("%H:%M") if attendance.sub_shift.time_start else None,
                    "time_end": attendance.sub_shift.time_end.strftime("%H:%M") if attendance.sub_shift.time_end else None
                }
            if attendance.is_late:
                response_data["late_minutes"] = attendance.late_by_minutes
                response_data["is_late"] = True
            
            # Check if checked out
            if attendance.date_check_out:
                response_data.update({
                    "status": "checked_out",
                    "check_out_time": attendance.date_check_out,
                    "working_hours": attendance.working_hour,
                    "message": "Employee checked out for the day"
                })
                
                # Add overtime information
                if attendance.overtime_minutes and attendance.overtime_minutes > 0:
                    response_data["overtime_minutes"] = attendance.overtime_minutes
                    response_data["overtime_hours"] = round(attendance.overtime_minutes / 60, 2)
                    response_data["is_overtime"] = True
                
                # Calculate early exit if applicable
                if attendance.sub_shift and attendance.sub_shift.time_end:
                    from .utils import validate_check_out_time
                    _, _, early_exit_minutes, _ = validate_check_out_time(
                        attendance.sub_shift, attendance.date_check_out, attendance.date_check_in
                    )
                    if early_exit_minutes > 0:
                        response_data["early_exit_minutes"] = early_exit_minutes
                        response_data["early_exit_hours"] = round(early_exit_minutes / 60, 2)
                        response_data["is_early_exit"] = True
            else:
                response_data.update({
                    "status": "checked_in",
                    "message": "Employee is currently checked in"
                })
            
            return response_data
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            return {"error": f"Error getting employee status: {str(e)}", "details": error_details, "status": "500"}


class LeaveService:
    """Service class for leave business logic"""
    
    @staticmethod
    def create_leave_request(data):
        """Create a new leave request"""
        try:
            attendance_type = AttendanceType.objects.get(id=data['attendance_type'], is_leave=True, deleted=False)
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
            data['attendance_type'], 
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
        leave_request.action_by = approver_id
        leave_request.action_at = timezone.now()
        leave_request.approval_remarks = approval_remarks
        leave_request.save()
        
        # Update leave balance
        LeaveService.update_leave_balance(leave_request.employee, leave_request.attendance_type.id, leave_request.total_days)
        
        return {
            "message": "Leave request approved successfully",
            "leave_request_id": leave_request.id,
            "approved_by": approver_id,
            "approved_at": str(leave_request.action_at)
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
        leave_request.action_by = approver_id
        leave_request.action_at = timezone.now()
        leave_request.approval_remarks = approval_remarks
        leave_request.save()
        
        return {
            "message": "Leave request rejected successfully",
            "leave_request_id": leave_request.id,
            "rejected_by": approver_id,
            "rejected_at": str(leave_request.action_at)
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
    
#     @staticmethod
#     def update_leave_balance(employee_id, attendance_type_id, used_days, year=None):
#         """Update leave balance after approval"""
#         if year is None:
#             year = timezone.now().year
        
#         try:
#             leave_balance = LeaveBalance.objects.get(
#                 employee=employee_id,
#                 leave_type_id=attendance_type_id,
#                 year=year,
#                 deleted=False
#             )
#             leave_balance.used_days += used_days
#             leave_balance.save()
#         except LeaveBalance.DoesNotExist:
#             # Create new balance record if doesn't exist
#             attendance_type = AttendanceType.objects.get(id=attendance_type_id)
#             LeaveBalance.objects.create(
#                 employee=employee_id,
#                 leave_type=attendance_type,
#                 year=year,
#                 total_days=0,
#                 used_days=used_days
#             )
    
#     @staticmethod
#     def get_employee_leave_balance(employee_id, year=None):
#         """Get employee's leave balance for all leave types"""
#         if year is None:
#             year = timezone.now().year
        
#         balances = LeaveBalance.objects.filter(
#             employee=employee_id,
#             year=year,
#             deleted=False
#         ).select_related('leave_type')
        
#         return balances


# class AttendanceReportService:
#     """Service class for attendance reporting"""
    
#     @staticmethod
#     def get_employee_attendance_summary(employee_id, date):
#         """Get attendance summary for employee"""
#         return get_attendance_summary(employee_id, date)
    
#     @staticmethod
#     def get_employee_status(employee_id, date):
#         """Get current employee status (checked in/out)"""
#         if not employee_id:
#             return format_error_response("employee parameter is required")
        
#         result = get_attendance_summary(employee_id, date)
#         return result
    
#     @staticmethod
#     def get_attendance_list(employee_id=None):
#         """Get attendance list with optional employee filtering"""
#         queryset = Attendance.objects.filter(deleted=False)
#         if employee_id:
#             queryset = queryset.filter(employee=employee_id)
#         return queryset.order_by('-date_check_in')
    
#     @staticmethod
#     def get_attendance_report(employee_id=None, start_date=None, end_date=None):
#         """Generate attendance report"""
#         queryset = Attendance.objects.filter(deleted=False)
        
#         if employee_id:
#             queryset = queryset.filter(employee=employee_id)
        
#         if start_date:
#             queryset = queryset.filter(date_check_in__date__gte=start_date)
        
#         if end_date:
#             queryset = queryset.filter(date_check_in__date__lte=end_date)
        
#         return queryset.order_by('-date_check_in')
    
#     @staticmethod
#     def auto_mark_absent_service(date=None):
#         """Auto-mark absent service"""
#         if date is None:
#             date = timezone.localdate()
#         auto_mark_absent(date)


# # Legacy functions (kept for backward compatibility)
# def get_all_employee_ids():
#     """Get all employee IDs (legacy function)"""
#     return get_employee_ids()


# def calculate_worked_minutes_legacy(attendance):
#     """Calculate worked minutes (legacy function)"""
#     return calculate_worked_minutes(attendance)


# def auto_mark_absent_legacy():
#     """Auto-mark absent (legacy function)"""
#     auto_mark_absent()


# def get_lop_days(employee_id, start_date, end_date):
#     """Get LOP days for employee in date range"""
#     lop_type = AttendanceType.objects.get(code='A')  # Or LOP type code
#     return Attendance.objects.filter(
#         employee=employee_id,
#         attendance_type=lop_type,
#         date_check_in__date__range=(start_date, end_date),
#         deleted=False
#     ).count()


# def calculate_lop_deduction(gross_salary, month_days, lop_days):
#     """Calculate LOP deduction from salary"""
#     return (gross_salary / month_days) * lop_days
