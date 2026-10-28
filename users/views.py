from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from users.models import User
from users.serializers import (
    UserRegisterSerializer,
    OrganisationRegisterSerializer,
    LoginSerializer,
    UserResponseSerializer,
)
from datetime import datetime
from django.db import transaction
from users.helper import get_tokens_for_user, generate_resource_slots
from users.redis_lock import slot_lock
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet
from resourses.models import *
from resourses.serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action


class ReservationPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserRegisterView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "User registered successfully",
                    "user": UserResponseSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganisationRegisterView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OrganisationRegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "Organisation registered successfully",
                    "user": UserResponseSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": f"{user.role.capitalize()} login successful",
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
   
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        data['role'] = User.USER
        serializer = LoginSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "User login successful",
                    "user": UserResponseSerializer(user).data,
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganisationLoginView(APIView):
    
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        data['role'] = User.ORGANISATION
        serializer = LoginSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)
            return Response(
                {
                    "message": "Organisation login successful",
                    "tokens": tokens,
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResourseViewSet(ModelViewSet):
    queryset = Resource.objects.filter(is_active=True)
    serializer_class = ResourseListSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"])
    def get_slot(self, request):
        resource_id = self.request.query_params.get('resource_id')
        date_str = self.request.query_params.get('date')
        
        if not resource_id:
            return Response({"message": "resource_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not date_str:
            return Response({'message': 'date is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking_date = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"message": "Invalid date format. Expected YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            resource = Resource.objects.get(id=resource_id)
        except (Resource.DoesNotExist, ValueError):
            return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

        if not resource.is_active:
            return Response({"message": "Resource is not active"}, status=status.HTTP_400_BAD_REQUEST)

        slots = generate_resource_slots(resource, booking_date)
        return Response({"message": "Slots fetched successfully", "slots": slots}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def make_resevation(self, request):
        resourse_id = request.data.get('resourse_id') or request.data.get('resource_id')
        start_time = request.data.get('start_time')
        end_time = request.data.get('end_time')
        date_str = request.data.get('date')

        if not resourse_id:
            return Response({"message": "resourse_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not date_str:
            return Response({"message": "date is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not start_time:
            return Response({"message": "start_time is required"}, status=status.HTTP_400_BAD_REQUEST)
        if not end_time:
            return Response({"message": "end_time is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resource = Resource.objects.get(id=resourse_id)
        except (Resource.DoesNotExist, ValueError):
            return Response({"message": "Resource not found"}, status=status.HTTP_404_NOT_FOUND)

        if not resource.is_active:
            return Response({"message": "Resource is not active"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking_date = datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"message": "Invalid date format. Expected YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        def parse_time(time_str):
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(str(time_str).strip(), fmt).time()
                except ValueError:
                    continue
            return None

        parsed_start = parse_time(start_time)
        parsed_end = parse_time(end_time)

        if not parsed_start or not parsed_end:
            return Response(
                {"message": "Invalid time format. Expected HH:MM or HH:MM:SS."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if parsed_start >= parsed_end:
            return Response({"message": "end_time must be after start_time"}, status=status.HTTP_400_BAD_REQUEST)

        if parsed_start < resource.slot_start_time or parsed_end > resource.slot_end_time:
            return Response(
                {"message": "Selected time is outside resource operating hours."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with slot_lock(resource.id, booking_date, parsed_start, user_id=request.user.id) as acquired:
            if not acquired:
                return Response(
                    {"message": "This slot is currently being reserved by another user. Please choose another slot or try again shortly."},
                    status=status.HTTP_409_CONFLICT,
                )

            with transaction.atomic():
                is_already_booked = Reservation.objects.filter(
                    resource=resource,
                    booking_date=booking_date,
                    booking_status=Reservation.BOOKED,
                    booking_slot_start_time__lt=parsed_end,
                    booking_slot_end_time__gt=parsed_start,
                ).exists()

                if is_already_booked:
                    return Response(
                        {"message": "This slot is already booked. Please choose another slot."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                reservation = Reservation.objects.create(
                    user=request.user,
                    resource=resource,
                    booking_date=booking_date,
                    booking_slot_start_time=parsed_start,
                    booking_slot_end_time=parsed_end,
                    booking_status=Reservation.BOOKED,
                )

        return Response(
            {
                "message": "Reservation made successfully",
                "reservation": ReservationSerializer(reservation).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"])
    def cancel_reservation(self, request):
        reservation_id = request.data.get('reservation_id') or request.data.get('id')
        if not reservation_id:
            return Response(
                {"message": "reservation_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reservation = Reservation.objects.get(id=reservation_id)
        except (Reservation.DoesNotExist, ValueError):
            return Response(
                {"message": "Reservation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check whether the reservation belongs to the requesting user
        if reservation.user != request.user:
            return Response(
                {"message": "You are not authorized to cancel this reservation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        if reservation.booking_status == Reservation.CANCELLED:
            return Response(
                {"message": "Reservation is already cancelled"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reservation.booking_status = Reservation.CANCELLED
        reservation.save()

        return Response(
            {
                "message": "Reservation cancelled successfully",
                "reservation": ReservationSerializer(reservation).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def user_reservations(self, request):
        
        reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')

        booking_status = request.query_params.get('status') or request.query_params.get('booking_status')
        if booking_status:
            reservations = reservations.filter(booking_status=booking_status.lower())

        paginator = ReservationPagination()
        page = paginator.paginate_queryset(reservations, request, view=self)
        if page is not None:
            serializer = ReservationSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ReservationSerializer(reservations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

