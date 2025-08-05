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


class LeaveSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveSetting
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']





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
    Serializer for attendance punch operations - Check In and Check Out
    """
    employee = serializers.IntegerField(help_text="Employee ID")
    action_type = serializers.IntegerField(help_text="Action ID - 1 for Check In, 2 for Check Out")
    source_id = serializers.IntegerField(required=False, help_text="Source ID (optional)")
    remarks = serializers.CharField(required=False, help_text="Additional remarks")
    custom_timestamp = serializers.DateTimeField(required=False, help_text="Custom timestamp for testing (optional)")
    
    def validate_employee(self, value):
        if value <= 0:
            raise serializers.ValidationError("Employee ID must be a positive integer")
        return value
    
    def validate_action_type(self, value):
        valid_action_ids = [1, 2]  # 1 for check_in, 2 for check_out
        if value not in valid_action_ids:
            raise serializers.ValidationError(f"Invalid action ID. Must be one of: {valid_action_ids} (1=Check In, 2=Check Out)")
        return value

class LeaveBalanceSummarySerializer(serializers.Serializer):
    """
    Serializer for leave balance summary
    """
    employee = serializers.IntegerField()
    leave_type = serializers.IntegerField()
    leave_type_name = serializers.CharField()
    total_days = serializers.IntegerField()
    used_days = serializers.IntegerField()
    remaining_days = serializers.IntegerField()
    year = serializers.IntegerField()


class LeaveRequestSummarySerializer(serializers.Serializer):
    """
    Serializer for leave request summary
    """
    employee = serializers.IntegerField()
    leave_type = serializers.IntegerField()
    leave_type_name = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    total_days = serializers.IntegerField()
    status = serializers.CharField()
    status_label = serializers.CharField()
    created_at = serializers.DateTimeField()


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'


class LeaveAllocationSerializer(serializers.ModelSerializer):
    attendance_type_name = serializers.CharField(source='attendance_type.title', read_only=True)
    
    class Meta:
        model = LeaveAllocation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']        