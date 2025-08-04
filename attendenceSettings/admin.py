from django.contrib import admin

# Register your models here.
from .models import *

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'is_active', 'deleted')
    search_fields = ('name', 'code')
    list_filter = ('is_active', 'deleted')
@admin.register(AttendanceType)
class AttendanceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title','code','color_code','is_leave', 'deleted')
    search_fields = ('title',)
    list_filter = ('deleted',)



@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'category', 'is_active', 'deleted')
    search_fields = ('name', 'code')
    list_filter = ('category', 'is_active', 'deleted')

# @admin.register(AttendancePunch)
# class AttendancePunchAdmin(admin.ModelAdmin):
#     list_display = ['id', 'employee', 'date', 'action', 'check_in_time', 'check_out_time', 'attendance', 'created_at']
#     list_filter = ['date', 'action']
#     search_fields = ['employee', 'action__name', 'attendance__employee']
#     ordering = ['-created_at']
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ( 'employee','company','attendance_type',
        'shift',
        'sub_shift',
        'action',
        'date_check_in',
        'date_check_out','working_hour',
        'source',
        'is_late',
        'late_by_minutes',
        'overtime_minutes',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'attendance_type',
        'shift',
        'sub_shift',
        'action',
        'source',
        'is_late',
        'deleted',
    )
    search_fields = ('employee',)


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'employee', 'attendance_type', 'start_date', 'end_date',
        'total_days', 'status', 'action_at', 'created_at'
    )
    list_filter = ('attendance_type', 'status', 'created_at')
    search_fields = ('employee', 'reason')
 
    readonly_fields = ('action_at', 'created_at', 'updated_at')


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'employee', 'leave_type', 'year',
        'total_days', 'used_days', 'remaining_days', 'deleted'
    )
    list_filter = ('year', 'leave_type', 'deleted')
    search_fields = ('employee',)
    ordering = ('-year', 'employee')

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display=(
        'code','label'

    )