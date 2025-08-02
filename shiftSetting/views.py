from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import ShiftHeadType, Shift, SubShift
from .serializers import *


#! shift head
class ShiftHeadTypeListView(APIView):
    def get(self, request):
        types = ShiftHeadType.objects.filter(is_deleted=False)
        serializer = ShiftHeadTypeSerializer(types, many=True)
        return Response({"data": serializer.data, "status": "200"})


class ShiftHeadTypeCreateView(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = ShiftHeadTypeSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ShiftHeadTypeRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = ShiftHeadType.objects.get(pk=pk, is_deleted=False)
            serializer = ShiftHeadTypeSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except ShiftHeadType.DoesNotExist:
            return Response({"error": "ShiftHeadType not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ShiftHeadTypeUpdateView(APIView):
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = ShiftHeadType.objects.get(pk=pk, is_deleted=False)
                serializer = ShiftHeadTypeSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except ShiftHeadType.DoesNotExist:
            return Response({"error": "ShiftHeadType not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ShiftHeadTypeDeleteView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = ShiftHeadType.objects.get(pk=pk, is_deleted=False)
                obj.is_deleted = True
                obj.save()
                return Response({"data": {"message": "Soft deleted"}, "status": "200"})
        except ShiftHeadType.DoesNotExist:
            return Response({"error": "ShiftHeadType not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


#! shift
class ShiftListView(APIView):
    def get(self, request):
        company_id = request.query_params.get('company_id')
        shifts = Shift.objects.filter(is_deleted=False)
        if company_id:
            shifts = shifts.filter(company_id=company_id)
        serializer = ShiftSerializer(shifts, many=True)
        return Response({"data": serializer.data, "status": "200"})


class ShiftCreateView(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = ShiftSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ShiftRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = Shift.objects.get(pk=pk, is_deleted=False)
            serializer = ShiftSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ShiftUpdateView(APIView):
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = Shift.objects.get(pk=pk, is_deleted=False)
                serializer = ShiftSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class ShiftDeleteView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = Shift.objects.get(pk=pk, is_deleted=False)
                obj.is_deleted = True
                obj.save()
                return Response({"data": {"message": "Soft deleted"}, "status": "200"})
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})



#! sub shift
class SubShiftListView(APIView):
    def get(self, request):
        shift_id = request.query_params.get('shift_id')
        sub_shifts = SubShift.objects.filter(is_deleted=False)
        if shift_id:
            sub_shifts = sub_shifts.filter(shift_id=shift_id)
        serializer = SubShiftSerializer(sub_shifts, many=True)
        return Response({"data": serializer.data, "status": "200"})


class SubShiftCreateView(APIView):
    def post(self, request):
        try:
            with transaction.atomic():
                serializer = SubShiftSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class SubShiftRetrieveView(APIView):
    def get(self, request, pk):
        try:
            obj = SubShift.objects.get(pk=pk, is_deleted=False)
            serializer = SubShiftSerializer(obj)
            return Response({"data": serializer.data, "status": "200"})
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class SubShiftUpdateView(APIView):
    def put(self, request, pk):
        try:
            with transaction.atomic():
                obj = SubShift.objects.get(pk=pk, is_deleted=False)
                serializer = SubShiftSerializer(obj, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response({"data": serializer.data, "status": "200"})
                return Response({"error": serializer.errors, "status": "500"})
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})


class SubShiftDeleteView(APIView):
    def delete(self, request, pk):
        try:
            with transaction.atomic():
                obj = SubShift.objects.get(pk=pk, is_deleted=False)
                obj.is_deleted = True
                obj.save()
                return Response({"data": {"message": "Soft deleted"}, "status": "200"})
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

