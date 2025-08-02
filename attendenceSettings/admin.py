from django.contrib import admin

# Register your models here.
from .models import *
@admin.register(AttendanceType)
class AttendanceTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'title','code','color_code', 'is_deleted')
    search_fields = ('title',)
    list_filter = ('is_deleted',)

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'attendance_type', 'date','shift','sub_shift', 'check_in_time', 'check_out_time', 'is_manual','source','late_by_minutes', 'overtime_minutes','remarks', 'created_at', 'updated_at')
    search_fields = ('employee__name', 'attendance_type__title')
    list_filter = ('attendance_type', 'date', 'is_manual')

@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'is_active', 'is_deleted')
    search_fields = ('name', 'code')
    list_filter = ('is_active', 'is_deleted')

@admin.register(AttendancePunch)
class AttendancePunchAdmin(admin.ModelAdmin):
    list_display = ['id', 'employee', 'date', 'action', 'check_in_time', 'check_out_time', 'attendance', 'created_at']
    list_filter = ['date', 'action']
    search_fields = ['employee', 'action__name', 'attendance__employee']
    ordering = ['-created_at']