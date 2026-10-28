from datetime import datetime, date, timedelta
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import AuthenticationFailed


def get_tokens_for_user(user):
    if not user.is_active:
        raise AuthenticationFailed("User is not active")

    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def generate_resource_slots(resource, date_input):
    """
    Generates time slots for a resource on a specific date based on
    slot_start_time, slot_end_time, and slot_interval.

    Checks Reservation for that date and marks is_booked=True
    if any active ('booked') reservation overlaps with the slot.
    """
    from resourses.models import Reservation

    if isinstance(date_input, str):
        booking_date = datetime.strptime(date_input.strip(), "%Y-%m-%d").date()
    elif isinstance(date_input, (datetime, date)):
        booking_date = date_input if isinstance(date_input, date) else date_input.date()
    else:
        raise ValueError("Invalid date input. Must be a date object or string formatted as YYYY-MM-DD.")

    interval_minutes = resource.slot_interval
    if not interval_minutes or interval_minutes <= 0:
        return []

    # Fetch active booked reservations for this resource on the given date
    booked_reservations = list(
        Reservation.objects.filter(
            resource=resource,
            booking_date=booking_date,
            booking_status=Reservation.BOOKED,
        ).values('booking_slot_start_time', 'booking_slot_end_time')
    )

    # Use a dummy date to perform time arithmetic with timedelta
    dummy_date = date(2000, 1, 1)
    current_start_dt = datetime.combine(dummy_date, resource.slot_start_time)
    end_limit_dt = datetime.combine(dummy_date, resource.slot_end_time)
    step = timedelta(minutes=interval_minutes)

    slots = []
    while current_start_dt + step <= end_limit_dt:
        current_end_dt = current_start_dt + step
        slot_start = current_start_dt.time()
        slot_end = current_end_dt.time()

        # A reservation overlaps with slot if:
        # res_start < slot_end AND res_end > slot_start
        is_booked = any(
            res['booking_slot_start_time'] < slot_end and res['booking_slot_end_time'] > slot_start
            for res in booked_reservations
        )

        from users.redis_lock import is_slot_locked
        is_locked = is_slot_locked(resource.id, booking_date, slot_start)

        slots.append({
            "start_time": slot_start.strftime("%H:%M:%S"),
            "end_time": slot_end.strftime("%H:%M:%S"),
            "is_booked": is_booked,
        })

        current_start_dt = current_end_dt

    return slots


# Alias for convenience
create_slots_for_resource = generate_resource_slots
get_resource_slots = generate_resource_slots