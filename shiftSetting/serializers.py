from rest_framework import serializers
from .models import *
class SubShiftSerializer(serializers.ModelSerializer):
    # Format time fields in HH:MM format
    time_start = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])
    time_end = serializers.TimeField(format="%H:%M", input_formats=["%H:%M", "%H:%M:%S"])

    class Meta:
        model = SubShift
        fields = '__all__'

class ShiftSerializer(serializers.ModelSerializer):
    sub_shifts = SubShiftSerializer(many=True, read_only=True)

    class Meta:
        model = Shift
        fields = '__all__'
