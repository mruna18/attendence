from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from .models import *
from .serializers import *

#! shift
class ShiftListView(APIView):
    def post(self, request):
        data = request.data
        company = data.get("company")
        shifts = Shift.objects.filter(deleted=False)
        if company:
            shifts = shifts.filter(company=company)
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
    def post(self, request):
        try:
            pk = request.data.get('id')
            if not pk:
                return Response({"error": "id is required", "status": "500"})
            obj = Shift.objects.get(pk=pk, deleted=False)
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
                obj = Shift.objects.get(pk=pk, deleted=False)
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
                obj = Shift.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Soft deleted", "status": "200"})
        except Shift.DoesNotExist:
            return Response({"error": "Shift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})



#! sub shift
class SubShiftListView(APIView):
    def post(self, request):
        data = request.data
        shift_id = data.get('shift_id')
        sub_shifts = SubShift.objects.filter(deleted=False)
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
    def post(self, request):
        try:
            pk = request.data.get('id')
            if not pk:
                return Response({"error": "id is required", "status": "500"})
            obj = SubShift.objects.get(pk=pk, deleted=False)
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
                obj = SubShift.objects.get(pk=pk, deleted=False)
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
                obj = SubShift.objects.get(pk=pk, deleted=False)
                obj.deleted = True
                obj.save()
                return Response({"data": "Soft deleted", "status": "200"})
        except SubShift.DoesNotExist:
            return Response({"error": "SubShift not found", "status": "500"})
        except Exception as e:
            return Response({"error": str(e), "status": "500"})

