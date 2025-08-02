from django.contrib import admin
from .models import *

@admin.register(ShiftHeadType)
class ShiftHeadTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'code', 'name')
    search_fields = ('code', 'name')

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'company_id', 'shift_head', 'description', 'created_at')
    list_filter = ('company_id', 'shift_head')
    search_fields = ('description',)

@admin.register(SubShift)
class SubShiftAdmin(admin.ModelAdmin):
    list_display = ('id', 'shift', 'title', 'time_start', 'time_end', 'active')
    list_filter = ('active',)
    search_fields = ('title',)
