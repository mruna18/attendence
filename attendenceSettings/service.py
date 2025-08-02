from datetime import datetime, timedelta
from django.utils import timezone
from .models import *


def calculate_worked_minutes(attendance):
    total_minutes = 0
    for punch in attendance.punches.all():
        if punch.check_in_time and punch.check_out_time:
            in_time = datetime.combine(attendance.date, punch.check_in_time)
            out_time = datetime.combine(attendance.date, punch.check_out_time)
            duration = int((out_time - in_time).total_seconds() / 60)
            total_minutes += max(0, duration)
    return total_minutes

# def get_all_employee_ids():
#     return Employee.objects.filter(is_deleted=False).values_list('id', flat=True)

def get_all_employee_ids():
    return Attendance.objects.values_list('employee', flat=True).distinct()

def auto_mark_absent():
    today = timezone.localdate()
    all_employee_ids = get_all_employee_ids()

    present_today = Attendance.objects.filter(date=today).values_list("employee", flat=True)

    for emp_id in all_employee_ids:
        if emp_id not in present_today:
            absent_type = AttendanceType.objects.get(code="A")
            Attendance.objects.create(
                employee=emp_id,
                date=today,
                attendance_type=absent_type,
                remarks="Auto-marked absent"
            )
