from datetime import datetime, timedelta
from collections import defaultdict

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny

from .models import TimeSlot, EventCategory
from .serializers import SlotSerializer

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from rest_framework import status

from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from rest_framework.decorators import api_view, permission_classes


class WeeklySlotsAPIView(APIView):
    permission_classes = [AllowAny]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user,"============")

        if request.user.is_staff:
            slots = TimeSlot.objects.all()

        week_start = request.query_params.get('week_start')
        category = request.query_params.get('category', 'All')

        start_date = datetime.strptime(week_start[:10], "%Y-%m-%d").date()
        end_date = start_date + timedelta(days=6)

        print("START:", start_date, "END:", end_date)

        slots = TimeSlot.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        )

        print("AFTER DATE FILTER:", slots.count())

        if category != 'All':
            slots = slots.filter(category__name=category)

        print("AFTER CATEGORY FILTER:", slots.count())

        day_map = defaultdict(list)

        for slot in slots:
            serializer = SlotSerializer(slot, context={'request': request})
            day_map[str(slot.date)].append(serializer.data)

        response = []
        for i in range(7):
            date = start_date + timedelta(days=i)
            response.append({
                "date": str(date),
                "slots": day_map.get(str(date), [])
            })

        return Response(response)

class BookSlotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, slot_id):
        try:
            with transaction.atomic():
                slot = TimeSlot.objects.select_for_update().get(id=slot_id)

                if slot.booked_by is not None:
                    return Response(
                        {"error": "Slot already booked"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                slot.booked_by = request.user
                slot.save()

        except TimeSlot.DoesNotExist:
            return Response(
                {"error": "Slot not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"message": "Slot booked successfully"},
            status=status.HTTP_200_OK
        )

# class BookSlotAPIView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, slot_id):
#         slot = TimeSlot.objects.select_for_update().get(id=slot_id)

#         if slot.booked_by:
#             return Response({"error": "Already booked"}, status=400)

#         slot.booked_by = request.user
#         slot.save()

#         return Response({"message": "Booked"})

class CancelBookingAPIView(APIView):
    permission_classes = [AllowAny]

    def delete(self, request, slot_id):
        try:
            slot = TimeSlot.objects.get(id=slot_id)
        except TimeSlot.DoesNotExist:
            return Response(
                {"error": "Slot not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        slot.booked_by = None
        slot.save()

        return Response(
            {"message": "Booking cancelled"},
            status=status.HTTP_200_OK
        )

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "username": user.username,
            "is_amin": user.is_staff
        })



class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create_user(
            username=username,
            password=password
        )

        return Response(
            {"message": "User registered successfully"},
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    return Response({
        "username": request.user.username,
        "is_staff": request.user.is_staff,
        "is_superuser": request.user.is_superuser,
    })


class AdminSlotsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Only admin can access
        if not request.user.is_staff:
            return Response(
                {"error": "Admin access required"},
                status=status.HTTP_403_FORBIDDEN
            )

        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        category = request.query_params.get('category', 'All')

        # Build query
        slots = TimeSlot.objects.all()

        if date_from:
            slots = slots.filter(date__gte=date_from)
        
        if date_to:
            slots = slots.filter(date__lte=date_to)

        if category != 'All':
            slots = slots.filter(category__name=category)

        # Format response
        response_data = []
        for slot in slots:
            response_data.append({
                "id": slot.id,
                "date": str(slot.date),
                "time": f"{slot.start_time.strftime('%I:%M %p')} – {slot.end_time.strftime('%I:%M %p')}",
                "category": slot.category.name,
                "status": "available" if slot.booked_by is None else "booked",
                "booked_by": slot.booked_by.username if slot.booked_by else None
            })

        return Response(response_data)


class AdminCreateSlotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Only admin can create slots
        if not request.user.is_staff:
            return Response({"error": "Admin access required"}, status=status.HTTP_403_FORBIDDEN)

        date_str = request.data.get('date')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        category_name = request.data.get('category')

        if not all([date_str, start_time_str, end_time_str, category_name]):
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date_val = datetime.strptime(date_str[:10], "%Y-%m-%d").date()
        except Exception:
            return Response({"error": "Invalid date format (expected YYYY-MM-DD)"}, status=status.HTTP_400_BAD_REQUEST)

        def parse_time(tstr):
            for fmt in ("%I:%M %p", "%H:%M"):
                try:
                    return datetime.strptime(tstr, fmt).time()
                except Exception:
                    continue
            raise ValueError("Invalid time format")

        try:
            start_time_val = parse_time(start_time_str)
            end_time_val = parse_time(end_time_str)
        except ValueError:
            return Response({"error": "Invalid time format (use 'HH:MM' or 'HH:MM AM/PM')"}, status=status.HTTP_400_BAD_REQUEST)

        category, _ = EventCategory.objects.get_or_create(name=category_name)

        slot = TimeSlot.objects.create(
            category=category,
            date=date_val,
            start_time=start_time_val,
            end_time=end_time_val,
        )

        serializer = SlotSerializer(slot, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)