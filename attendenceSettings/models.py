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
    category = models.CharField(max_length=20, choices=[
        ('attendance', 'Attendance'),
        ('break', 'Break'),
        ('leave', 'Leave'),
        ('other', 'Other')
    ], default='attendance')
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
    title = models.CharField(max_length=100,null=True, blank=True)  # e.g., Present, Absent, Leave
    code = models.CharField(max_length=10, unique=True,null=True, blank=True)  # e.g., P, A, W, CO
    color_code = models.CharField(max_length=7, blank=True, null=True)  # e.g., #FF0000
    # company = models.ForeignKey(Company, on_delete=models.DO_NOTHING,blank=True, null=True)
    company = models.IntegerField(blank=True, null=True)
    is_leave = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    def __str__(self):
        try:
            title = self.title if self.title else 'Unknown'
            code = self.code if self.code else 'No Code'
            return f"{title} ({code})"
        except Exception:
            return "Unknown Attendance Type"


# class Attendance(models.Model):
#     # employee = models.ForeignKey('api.Employee', on_delete=models.DO_NOTHING,null=True, blank=True)
#     employee = models.IntegerField( null=True, blank=True)
#     # company = models.ForeignKey(Company, on_delete=models.DO_NOTHING,blank=True, null=True)
#     company = models.IntegerField(blank=True, null=True)
#     # date = models.DateField(null=True, blank=True)

#     attendance_type = models.ForeignKey('AttendanceType', on_delete=models.DO_NOTHING,null=True, blank=True)
#     shift = models.ForeignKey('shiftSetting.Shift', on_delete=models.DO_NOTHING, null=True, blank=True)
#     sub_shift = models.ForeignKey('shiftSetting.SubShift', on_delete=models.DO_NOTHING, null=True, blank=True)

#     # check_in_time = models.TimeField(null=True, blank=True)
#     # check_out_time = models.TimeField(null=True, blank=True)

#     date_check_in = models.DateTimeField(null=True,blank=True)

#     # location = models.TextField( null=True, blank=True)
#     source = models.ForeignKey(Source, on_delete=models.DO_NOTHING,null=True, blank=True)

#     remarks = models.TextField(blank=True, null=True)
#     deleted = models.BooleanField(default=False)
#     is_late = models.BooleanField(default=False)

#     late_by_minutes = models.PositiveIntegerField(null=True, blank=True)
#     overtime_minutes = models.FloatField(null=True, blank=True)

#     created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
#     updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

#     class Meta:
#         unique_together = ['employee', 'date']
#         ordering = ['-date']

#     def __str__(self):
#         return f"{self.employee} - {self.date} - {self.attendance_type.code if self.attendance_type else 'No Type'}"


# #! attendance for multople puching
# class AttendancePunch(models.Model):
#     employee = models.IntegerField(null=True, blank=True) 
#     date = models.DateField(null=True, blank=True) 
#     action = models.ForeignKey('Action', on_delete=models.DO_NOTHING,null=True, blank=True) 
#     check_in_time = models.TimeField(null=True, blank=True) 
#     check_out_time = models.TimeField(null=True, blank=True)  # Optional for check-out
#     attendance = models.ForeignKey('Attendance', on_delete=models.DO_NOTHING, related_name='punches',null=True, blank=True) 
#     created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

#     class Meta:
#         ordering = ['-created_at']

#     def __str__(self):
#         return f"{self.employee} - {self.date} - {self.action.name} at {self.check_in_time}"

class Attendance(models.Model):
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
    code = models.CharField(max_length=50, unique=True)   # e.g., "p", "a"
    label = models.CharField(max_length=100)              # e.g., "Pending", "Approved"
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return self.label
class LeaveRequest(models.Model):
    """
    Model to handle leave requests
    """
    employee = models.IntegerField(null=True, blank=True)  #! Employee ID fk
    company = models.IntegerField(null=True, blank=True)  #! fk
    attendance_type = models.ForeignKey(AttendanceType, on_delete=models.DO_NOTHING,null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    total_days = models.PositiveIntegerField(null=True, blank=True)  # Calculated field
    reason = models.TextField(null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.DO_NOTHING,null=True, blank=True)
    
    # Approval fields
    action_by = models.IntegerField(null=True, blank=True)  #! Approver employee ID
    action_at = models.DateTimeField(null=True, blank=True)
    approval_remarks = models.TextField(blank=True, null=True)
    

    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True) #! blob storage
    
    deleted = models.BooleanField(default=False,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

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
    employee = models.IntegerField(null=True, blank=True)  # Employee ID
    # company = models.IntegerField(null=True, blank=True)  # company ID
    leave_type = models.ForeignKey(AttendanceType, on_delete=models.DO_NOTHING,null=True, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)  # Year for which balance is tracked
    total_days = models.PositiveIntegerField(null=True, blank=True)  # Total days allocated
    used_days = models.PositiveIntegerField(default=0,null=True, blank=True)  # Days used
    remaining_days = models.PositiveIntegerField(default=0,null=True, blank=True)  # Days remaining
    deleted = models.BooleanField(default=False,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    class Meta:
        unique_together = ['employee', 'leave_type', 'year']
        ordering = ['-year', 'leave_type__title']

    def __str__(self):
        try:
            leave_type_title = self.leave_type.title if self.leave_type else 'No Type'
            return f"{self.employee} - {leave_type_title} - {self.year}"
        except Exception:
            return f"{self.employee} - Unknown Type - {self.year}"

    def save(self, *args, **kwargs):
        # Calculate remaining days
        if self.total_days is not None and self.used_days is not None:
            self.remaining_days = self.total_days - self.used_days
        super().save(*args, **kwargs)


#! leave ssetting 

#! mapping employee and leaves