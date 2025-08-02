from rest_framework import serializers
from .models import *

class ActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Action
        fields = '__all__'


class AttendanceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttendanceType
        fields = '__all__'


class AttendanceSerializer(serializers.ModelSerializer):
    check_in_time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"], required=False)
    check_out_time = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"], required=False)

    class Meta:
        model = Attendance
        fields = '__all__'


class AttendancePunchSerializer(serializers.Serializer):
    """
    Serializer for attendance punch operations
    """
    employee = serializers.IntegerField(help_text="Employee ID")
    action = serializers.IntegerField(help_text="Action ID (e.g., 1 for Check In, 2 for Check Out)")
    
    def validate_employee(self, value):
        if value <= 0:
            raise serializers.ValidationError("Employee ID must be a positive integer")
        return value
    
    def validate_action(self, value):
        try:
            Action.objects.get(id=value, is_active=True, is_deleted=False)
        except Action.DoesNotExist:
            raise serializers.ValidationError("Invalid action ID or action is not active")
        return value
        