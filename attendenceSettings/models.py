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
    is_deleted = models.BooleanField(default=False)
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
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.code})"


class Attendance(models.Model):
    # employee = models.ForeignKey('api.Employee', on_delete=models.DO_NOTHING,null=True, blank=True)
    employee = models.IntegerField( null=True, blank=True)
    date = models.DateField(null=True, blank=True)

    attendance_type = models.ForeignKey('AttendanceType', on_delete=models.DO_NOTHING,null=True, blank=True)
    shift = models.ForeignKey('shiftSetting.Shift', on_delete=models.DO_NOTHING, null=True, blank=True)
    sub_shift = models.ForeignKey('shiftSetting.SubShift', on_delete=models.DO_NOTHING, null=True, blank=True)

    check_in_time = models.TimeField(null=True, blank=True)
    check_out_time = models.TimeField(null=True, blank=True)

    # location = models.( null=True, blank=True)
    source = models.CharField(max_length=50, blank=True, null=True)  # e.g., "Web", "Biometric", "Mobile App"
    # verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    remarks = models.TextField(blank=True, null=True)
    is_manual = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    late_by_minutes = models.PositiveIntegerField(null=True, blank=True)
    overtime_minutes = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True,null=True, blank=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.attendance_type.code if self.attendance_type else 'No Type'}"


#! attendance for multople puching
class AttendancePunch(models.Model):
    employee = models.IntegerField()  # Required field
    date = models.DateField()  # Required field
    action = models.ForeignKey('Action', on_delete=models.CASCADE)  # Required field
    check_in_time = models.TimeField()  # Required field
    check_out_time = models.TimeField(null=True, blank=True)  # Optional for check-out
    attendance = models.ForeignKey('Attendance', on_delete=models.CASCADE, related_name='punches')  # Required field
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee} - {self.date} - {self.action.name} at {self.check_in_time}"
