from rest_framework import serializers
from .models import *

class LeaveRequestSerializer(serializers.ModelSerializer):
    attendance_type_name = serializers.CharField(source='attendance_type.title', read_only=True)
    status_label = serializers.CharField(source='status.label', read_only=True)
    
    class Meta:
        model = LeaveRequest
        fields = '__all__'
        read_only_fields = ['total_days', 'approved_at', 'created_at', 'updated_at']

    def validate(self, data):
        # Validate date range
        if data.get('start_date') and data.get('end_date'):
            if data['start_date'] > data['end_date']:
                raise serializers.ValidationError("End date cannot be before start date")
        return data


class LeaveBalanceSerializer(serializers.ModelSerializer):
    leave_type_name = serializers.CharField(source='leave_type.title', read_only=True)
    
    class Meta:
        model = LeaveBalance
        fields = '__all__'
        read_only_fields = ['remaining_days', 'created_at', 'updated_at']


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = '__all__'


class AttendanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceType
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    attendance_type_name = serializers.CharField(source='attendance_type.title', read_only=True)
    
    class Meta:
        model = Attendance
        fields = '__all__'


class AttendancePunchSerializer(serializers.Serializer):
    """
    Serializer for attendance punch operations
    """
    employee = serializers.IntegerField(help_text="Employee ID")
    action_type = serializers.ChoiceField(
        choices=[
            ('check_in', 'Check In'),
            ('check_out', 'Check Out'),
            ('break_start', 'Break Start'),
            ('break_end', 'Break End'),
            ('lunch_start', 'Lunch Start'),
            ('lunch_end', 'Lunch End'),
            ('half_day', 'Half Day'),
            ('wfh', 'Work From Home'),
        ],
        help_text="Type of attendance action"
    )
    source_id = serializers.IntegerField(required=False, help_text="Source ID (optional)")
    remarks = serializers.CharField(required=False, help_text="Additional remarks")
    
    def validate_employee(self, value):
        if value <= 0:
            raise serializers.ValidationError("Employee ID must be a positive integer")
        return value
    
    def validate_action_type(self, value):
        valid_actions = [
            'check_in', 'check_out', 'break_start', 'break_end',
            'lunch_start', 'lunch_end', 'half_day', 'wfh'
        ]
        if value not in valid_actions:
            raise serializers.ValidationError(f"Invalid action type. Must be one of: {valid_actions}")
        return value
        