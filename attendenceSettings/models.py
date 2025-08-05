from django.db import models
from django.conf import settings
from shiftSetting.models import *

class Action(models.Model):
    """
    Model to handle different attendance actions
    """
    name = models.CharField(max_length=50, unique=True)  # e.g., "Check In", "Check Out", "Break Start"
    code = models.CharField(max_length=20, unique=True)  # e.g., "check_in", "check_out", "break_start"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Source(models.Model):
    """
    Model to handle different attendance sources
    """
    name = models.CharField(max_length=100, unique=True)  # e.g., "Web Portal", "Biometric Device", "Mobile App"
    code = models.CharField(max_length=20, unique=True)   # e.g., "WEB", "BIOMETRIC", "MOBILE"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"
    

class AttendanceType(models.Model):
    title = models.CharField(max_length=100, null=True, blank=True)  # e.g., Present, Absent, Leave
    code = models.CharField(max_length=10, unique=True, null=True, blank=True)  # e.g., P, A, W, CO
    color_code = models.CharField(max_length=7, blank=True, null=True)  # e.g., #FF0000
    company = models.IntegerField(blank=True, null=True)
    is_leave = models.BooleanField(default=False)
    
    # Leave allocation fields (only used when is_leave=True)
    default_allotted_days = models.PositiveIntegerField(default=0, help_text="Default allotted days for this leave type")
    max_allotted_days = models.PositiveIntegerField(default=365, help_text="Maximum allotted days allowed")
    is_paid_leave = models.BooleanField(default=True, help_text="Whether this is a paid leave")
    is_medical_leave = models.BooleanField(default=False, help_text="Whether this is a medical leave")
    requires_approval = models.BooleanField(default=True, help_text="Whether approval is required")
    requires_attachment = models.BooleanField(default=False, help_text="Whether attachment is required")
    
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        try:
            title = self.title if self.title else 'Unknown'
            code = self.code if self.code else 'No Code'
            return f"{title} ({code})"
        except Exception:
            return "Unknown Attendance Type"
    
    def get_allotted_days_for_employee(self, employee_id, year=None):
        """Get allotted days for a specific employee and year"""
        if not self.is_leave:
            return 0
            
        if year is None:
            year = timezone.now().year
        
        try:
            leave_allocation = LeaveAllocation.objects.get(
                employee=employee_id,
                attendance_type=self,
                financial_year=year,
                deleted=False
            )
            return leave_allocation.allotted_days
        except LeaveAllocation.DoesNotExist:
            return self.default_allotted_days


class Attendance(models.Model):
    """
    Main attendance model for check-in and check-out records
    """
    employee = models.IntegerField(null=True, blank=True)
    company = models.IntegerField(null=True, blank=True)
    
    attendance_type = models.ForeignKey('AttendanceType', on_delete=models.DO_NOTHING, null=True, blank=True)
    shift = models.ForeignKey('shiftSetting.Shift', on_delete=models.DO_NOTHING, null=True, blank=True)
    sub_shift = models.ForeignKey('shiftSetting.SubShift', on_delete=models.DO_NOTHING, null=True, blank=True)

    action = models.ForeignKey('Action', on_delete=models.DO_NOTHING, null=True, blank=True)
    date_check_in = models.DateTimeField(null=True, blank=True) 
    date_check_out = models.DateTimeField(null=True, blank=True)  

    source = models.ForeignKey(Source, on_delete=models.DO_NOTHING, null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)

    is_late = models.BooleanField(default=False)
    late_by_minutes = models.PositiveIntegerField(null=True, blank=True)
    overtime_minutes = models.FloatField(null=True, blank=True)
    working_hour = models.FloatField(null=True, blank=True)

    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date_check_in']

    def __str__(self):
        try:
            action_name = self.action.name if self.action else 'Unknown'
            check_in_time = self.date_check_in.strftime("%Y-%m-%d %H:%M") if self.date_check_in else 'No Time'
            return f"{self.employee} - {action_name} at {check_in_time}"
        except Exception:
            return f"{self.employee} - Unknown Action"


class Status(models.Model):
    """
    Model to handle different status types (Pending, Approved, Rejected, etc.)
    """
    code = models.CharField(max_length=50, unique=True)   # e.g., "pending", "approved", "rejected"
    label = models.CharField(max_length=100)              # e.g., "Pending", "Approved", "Rejected"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.label


class LeaveAllocation(models.Model):
    """
    Model to manage employee-specific leave allocations
    """
    employee = models.IntegerField(null=True, blank=True)  # FK to Employee
    company = models.IntegerField(null=True, blank=True)   # FK to Company
    attendance_type = models.ForeignKey(AttendanceType, on_delete=models.DO_NOTHING, null=True, blank=True)
    
    financial_year = models.PositiveIntegerField(default=2024, help_text="Financial year (e.g., 2024)")
    allotted_days = models.PositiveIntegerField(default=0, help_text="Allotted days for this employee and leave type")
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'company', 'attendance_type', 'financial_year')
        verbose_name = "Leave Allocation"
        verbose_name_plural = "Leave Allocations"

    def __str__(self):
        return f"{self.employee} - {self.attendance_type} - FY {self.financial_year} ({self.allotted_days} days)"


class LeaveRequest(models.Model):
    """
    Model to handle leave requests
    """
    employee = models.IntegerField(null=True, blank=True)
    company = models.IntegerField(null=True, blank=True)
    attendance_type = models.ForeignKey(AttendanceType, on_delete=models.DO_NOTHING, null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    total_days = models.PositiveIntegerField(null=True, blank=True)  # Calculated field
    reason = models.TextField(null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING, null=True, blank=True)
    
    # Approval fields
    action_by = models.IntegerField(null=True, blank=True)  # Approver employee ID
    action_at = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True, null=True)
    
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)
    
    deleted = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        try:
            attendance_type_title = self.attendance_type.title if self.attendance_type else 'No Type'
            return f"{self.employee} - {attendance_type_title} - {self.start_date} to {self.end_date}"
        except Exception:
            return f"{self.employee} - Unknown Type - {self.start_date} to {self.end_date}"

    def save(self, *args, **kwargs):
        # Calculate total days if not set
        if not self.total_days and self.start_date and self.end_date:
            from datetime import date
            delta = self.end_date - self.start_date
            self.total_days = delta.days + 1  # Include both start and end dates
        super().save(*args, **kwargs)


class LeaveBalance(models.Model):
    """
    Model to track employee leave balances
    """
    employee = models.IntegerField(null=True, blank=True)
    attendance_type = models.ForeignKey(AttendanceType, on_delete=models.DO_NOTHING, null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)  # Financial year for which balance is tracked
    total_days = models.PositiveIntegerField(null=True, blank=True)  # Total days allocated
    used_days = models.PositiveIntegerField(default=0, null=True, blank=True)  # Days used
    remaining_days = models.PositiveIntegerField(default=0, null=True, blank=True)  # Days remaining
    deleted = models.BooleanField(default=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        unique_together = ['employee', 'attendance_type', 'year']
        ordering = ['-year', 'attendance_type__title']

    def __str__(self):
        try:
            attendance_type_title = self.attendance_type.title if self.attendance_type else 'No Type'
            return f"{self.employee} - {attendance_type_title} - {self.year}"
        except Exception:
            return f"{self.employee} - Unknown Type - {self.year}"

    def save(self, *args, **kwargs):
        # Calculate remaining days
        if self.total_days is not None and self.used_days is not None:
            self.remaining_days = self.total_days - self.used_days
        super().save(*args, **kwargs) 


class LeaveType(models.Model):
    """
    Model to manage leave types and their allocated days
    """
    name = models.CharField(max_length=100, help_text="Leave type name (e.g., Annual Leave, Sick Leave)")
    code = models.CharField(max_length=10, unique=True, help_text="Leave type code (e.g., AL, SL, CL)")
    description = models.TextField(blank=True, null=True, help_text="Description of the leave type")
    
    # Allocation settings
    default_allotted_days = models.PositiveIntegerField(default=0, help_text="Default allotted days for this leave type")
    max_allotted_days = models.PositiveIntegerField(default=365, help_text="Maximum allotted days allowed")
    
    # Leave type settings
    is_paid_leave = models.BooleanField(default=True, help_text="Whether this is a paid leave")
    is_medical_leave = models.BooleanField(default=False, help_text="Whether this is a medical leave")
    is_emergency_leave = models.BooleanField(default=False, help_text="Whether this is an emergency leave")
    requires_approval = models.BooleanField(default=True, help_text="Whether approval is required")
    requires_attachment = models.BooleanField(default=False, help_text="Whether attachment is required")
    
    # Color and display
    color_code = models.CharField(max_length=7, default="#007bff", help_text="Color code for display")
    
    # Status
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"

    def __str__(self):
        return f"{self.name} ({self.code})"

    def get_allotted_days_for_employee(self, employee_id, year=None):
        """Get allotted days for a specific employee and year"""
        if year is None:
            year = timezone.now().year
        
        try:
            leave_setting = LeaveSetting.objects.get(
                employee=employee_id,
                leave_type=self,
                financial_year_start__year=year,
                deleted=False
            )
            return leave_setting.allotted_days
        except LeaveSetting.DoesNotExist:
            return self.default_allotted_days


class LeaveSetting(models.Model):
    """
    Model to manage employee-specific leave settings
    """
    employee = models.IntegerField(null=True, blank=True)  # FK to Employee
    company = models.IntegerField(null=True, blank=True)   # FK to Company
    leave_type = models.ForeignKey(LeaveType, on_delete=models.DO_NOTHING, null=True, blank=True)
    
    financial_year_start = models.DateField(null=True, blank=True)  # e.g., 2025-04-01
    financial_year_end = models.DateField(null=True, blank=True)    # e.g., 2026-03-31
    allotted_days = models.PositiveIntegerField(default=0, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'company', 'leave_type', 'financial_year_start')
        verbose_name = "Leave Setting"
        verbose_name_plural = "Leave Settings"

    def __str__(self):
        return f"{self.employee} - {self.leave_type} - FY {self.financial_year_start.year if self.financial_year_start else 'N/A'}"


class LeaveDetail(models.Model):
    company = models.IntegerField(null=True, blank=True)   # FK to Company
    leave_type = models.ForeignKey(LeaveType, on_delete=models.DO_NOTHING, null=True, blank=True)
    
    financial_year_start = models.DateField(null=True, blank=True)  # e.g., 2025-04-01
    financial_year_end = models.DateField(null=True, blank=True)    # e.g., 2026-03-31
    
    allotted_days = models.PositiveIntegerField(default=0, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        unique_together = ('company', 'leave_type', 'financial_year_start')
