from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ShiftHeadType, Shift, SubShift
from .serializers import *


#! shift head
class ShiftHeadTypeListView(APIView):
    def get(self, request):
        types = ShiftHeadType.objects.filter(is_deleted=False)
        serializer = ShiftHeadTypeSerializer(types, many=True)
        return Response(serializer.data)


class ShiftHeadTypeCreateView(APIView):
    def post(self, request):
        serializer = ShiftHeadTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShiftHeadTypeRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = ShiftHeadType.objects.get(pk=pk, is_deleted=False)
        except ShiftHeadType.DoesNotExist:
            return Response({"error": "ShiftHeadType not found"}, status=404)
        serializer = ShiftHeadTypeSerializer(obj)
        return Response(serializer.data)


class ShiftHeadTypeUpdateView(APIView):
    def put(self, request, pk):
        try:
            obj = ShiftHeadType.objects.get(pk=pk, is_deleted=False)
        except ShiftHeadType.DoesNotExist:
            return Response({"error": "ShiftHeadType not found"}, status=404)
        serializer = ShiftHeadTypeSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ShiftHeadTypeDeleteView(APIView):
    def delete(self, request, pk):
        try:
            obj = ShiftHeadType.objects.get(pk=pk, is_deleted=False)
        except ShiftHeadType.DoesNotExist:
            return Response({"error": "ShiftHeadType not found"}, status=404)
        obj.is_deleted = True
        obj.save()
        return Response({"message": "ShiftHeadType soft deleted."}, status=200)


#! shift
class ShiftListView(APIView):
    def get(self, request):
        company_id = request.query_params.get('company_id')
        shifts = Shift.objects.filter(is_deleted=False)
        if company_id:
            shifts = shifts.filter(company_id=company_id)
        serializer = ShiftSerializer(shifts, many=True)
        return Response(serializer.data)


class ShiftCreateView(APIView):
    def post(self, request):
        serializer = ShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShiftRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = Shift.objects.get(pk=pk, is_deleted=False)
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found"}, status=404)
        serializer = ShiftSerializer(obj)
        return Response(serializer.data)


class ShiftUpdateView(APIView):
    def put(self, request, pk):
        try:
            obj = Shift.objects.get(pk=pk, is_deleted=False)
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found"}, status=404)
        serializer = ShiftSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ShiftDeleteView(APIView):
    def delete(self, request, pk):
        try:
            obj = Shift.objects.get(pk=pk, is_deleted=False)
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found"}, status=404)
        obj.is_deleted = True
        obj.save()
        return Response({"message": "Shift soft deleted."}, status=200)



#! sub shift
class SubShiftListView(APIView):
    def get(self, request):
        shift_id = request.query_params.get('shift_id')
        sub_shifts = SubShift.objects.filter(is_deleted=False)
        if shift_id:
            sub_shifts = sub_shifts.filter(shift_id=shift_id)
        serializer = SubShiftSerializer(sub_shifts, many=True)
        return Response(serializer.data)


class SubShiftCreateView(APIView):
    def post(self, request):
        serializer = SubShiftSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubShiftRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = SubShift.objects.get(pk=pk, is_deleted=False)
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found"}, status=404)
        serializer = SubShiftSerializer(obj)
        return Response(serializer.data)


class SubShiftUpdateView(APIView):
    def put(self, request, pk):
        try:
            obj = SubShift.objects.get(pk=pk, is_deleted=False)
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found"}, status=404)
        serializer = SubShiftSerializer(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class SubShiftDeleteView(APIView):
    def delete(self, request, pk):
        try:
            obj = SubShift.objects.get(pk=pk, is_deleted=False)
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found"}, status=404)
        obj.is_deleted = True
        obj.save()
        return Response({"message": "SubShift soft deleted."}, status=200)

