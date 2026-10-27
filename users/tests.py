from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User


class AuthAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration_success(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(reverse('user-register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertEqual(response.data["user"]["role"], User.USER)
        self.assertEqual(response.data["user"]["email"], "john.doe@example.com")
        self.assertTrue(User.objects.filter(email="john.doe@example.com").exists())

    def test_user_registration_missing_fields(self):
        data = {
            "first_name": "John",
            "email": "incomplete@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(reverse('user-register'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("last_name", response.data)

    def test_organisation_registration_success(self):
        data = {
            "email": "contact@acme.org",
            "password": "orgpassword123",
            "organisation_name": "Acme Corporation",
        }
        response = self.client.post(reverse('organisation-register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertEqual(response.data["user"]["role"], User.ORGANISATION)
        self.assertEqual(response.data["user"]["email"], "contact@acme.org")
        self.assertEqual(response.data["user"]["organisation_name"], "Acme Corporation")

    def test_organisation_registration_email_and_password_only(self):
        data = {
            "email": "info@startup.io",
            "password": "startuppassword123",
        }
        response = self.client.post(reverse('organisation-register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["user"]["role"], User.ORGANISATION)

    def test_user_login_success(self):
        User.objects.create_user(
            email="login_user@example.com",
            password="userpassword123",
            first_name="Alice",
            last_name="Smith",
            role=User.USER,
        )
        data = {
            "email": "login_user@example.com",
            "password": "userpassword123",
        }
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("User login successful", response.data["message"])

    def test_organisation_login_success(self):
        User.objects.create_user(
            email="login_org@example.com",
            password="orgpassword123",
            organisation_name="Tech Solutions",
            role=User.ORGANISATION,
        )
        data = {
            "email": "login_org@example.com",
            "password": "orgpassword123",
        }
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", response.data)
        self.assertIn("Organisation login successful", response.data["message"])

    def test_login_invalid_password(self):
        User.objects.create_user(
            email="valid@example.com",
            password="correctpassword",
            first_name="Bob",
            last_name="Marley",
        )
        data = {
            "email": "valid@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(reverse('login'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_email_registration(self):
        User.objects.create_user(
            email="duplicate@example.com",
            password="password123",
            first_name="Original",
            last_name="User",
        )
        data = {
            "first_name": "New",
            "last_name": "User",
            "email": "duplicate@example.com",
            "password": "newpassword123",
        }
        response = self.client.post(reverse('user-register'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_slot_success_and_booking_status(self):
        from datetime import time, date
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="slot_org@example.com",
            password="orgpassword123",
            organisation_name="Org Tech",
            role=User.ORGANISATION,
        )
        user = User.objects.create_user(
            email="booker@example.com",
            password="userpassword123",
            first_name="Sam",
            last_name="Wilson",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Study Room")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Study Room 1",
            slot_interval=30,
            slot_start_time=time(10, 0),
            slot_end_time=time(12, 0),
        )

        # Create a reservation for 10:30 - 11:00
        test_date = date(2026, 11, 1)
        Reservation.objects.create(
            user=user,
            resource=resource,
            booking_status=Reservation.BOOKED,
            booking_date=test_date,
            booking_slot_start_time=time(10, 30),
            booking_slot_end_time=time(11, 0),
        )

        self.client.force_authenticate(user=user)
        response = self.client.get(
            reverse('user-resource-get-slot'),
            {'resource_id': resource.id, 'date': '2026-11-01'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("slots", response.data)
        slots = response.data["slots"]
        self.assertEqual(len(slots), 4)

        # Slot 1: 10:00 - 10:30 -> is_booked False
        self.assertEqual(slots[0]["start_time"], "10:00:00")
        self.assertEqual(slots[0]["end_time"], "10:30:00")
        self.assertFalse(slots[0]["is_booked"])

        # Slot 2: 10:30 - 11:00 -> is_booked True
        self.assertEqual(slots[1]["start_time"], "10:30:00")
        self.assertEqual(slots[1]["end_time"], "11:00:00")
        self.assertTrue(slots[1]["is_booked"])

        # Slot 3: 11:00 - 11:30 -> is_booked False
        self.assertFalse(slots[2]["is_booked"])

    def test_get_slot_missing_params(self):
        user = User.objects.create_user(
            email="param_test@example.com",
            password="userpassword123",
            first_name="Test",
            last_name="User",
        )
        self.client.force_authenticate(user=user)

        # Missing date
        response = self.client.get(reverse('user-resource-get-slot'), {'resource_id': 1})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Missing resource_id
        response = self.client.get(reverse('user-resource-get-slot'), {'date': '2026-11-01'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_make_reservation_success(self):
        from datetime import time
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="res_org@example.com",
            password="orgpassword123",
            organisation_name="Org Tech",
            role=User.ORGANISATION,
        )
        user = User.objects.create_user(
            email="booker_res@example.com",
            password="userpassword123",
            first_name="Alice",
            last_name="Wonder",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Lab")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Chemistry Lab",
            slot_interval=60,
            slot_start_time=time(9, 0),
            slot_end_time=time(17, 0),
        )

        self.client.force_authenticate(user=user)
        payload = {
            "resourse_id": resource.id,
            "date": "2026-11-05",
            "start_time": "10:00:00",
            "end_time": "11:00:00",
        }
        response = self.client.post(reverse('user-resource-make-resevation'), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["message"], "Reservation made successfully")
        self.assertTrue(
            Reservation.objects.filter(
                resource=resource,
                user=user,
                booking_date="2026-11-05",
                booking_status=Reservation.BOOKED,
            ).exists()
        )

    def test_make_reservation_double_booking_rejected(self):
        from datetime import time, date
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="res_org2@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        user1 = User.objects.create_user(
            email="user1@example.com",
            password="userpassword123",
            first_name="User",
            last_name="One",
            role=User.USER,
        )
        user2 = User.objects.create_user(
            email="user2@example.com",
            password="userpassword123",
            first_name="User",
            last_name="Two",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Studio")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Music Studio",
            slot_interval=60,
            slot_start_time=time(9, 0),
            slot_end_time=time(17, 0),
        )

        # Existing reservation by user1
        Reservation.objects.create(
            user=user1,
            resource=resource,
            booking_date=date(2026, 11, 10),
            booking_slot_start_time=time(14, 0),
            booking_slot_end_time=time(15, 0),
            booking_status=Reservation.BOOKED,
        )

        # user2 tries to book overlapping slot (14:00 - 15:00)
        self.client.force_authenticate(user=user2)
        payload = {
            "resourse_id": resource.id,
            "date": "2026-11-10",
            "start_time": "14:00:00",
            "end_time": "15:00:00",
        }
        response = self.client.post(reverse('user-resource-make-resevation'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already booked", response.data["message"])

    def test_make_reservation_outside_operating_hours(self):
        from datetime import time
        from resourses.models import ResourseCategory, Resource

        org = User.objects.create_user(
            email="res_org3@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        user = User.objects.create_user(
            email="user3@example.com",
            password="userpassword123",
            first_name="User",
            last_name="Three",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Gym")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Squash Court",
            slot_interval=30,
            slot_start_time=time(9, 0),
            slot_end_time=time(12, 0),
        )

        self.client.force_authenticate(user=user)
        # Booking after end_time 12:00
        payload = {
            "resourse_id": resource.id,
            "date": "2026-11-12",
            "start_time": "12:00:00",
            "end_time": "12:30:00",
        }
        response = self.client.post(reverse('user-resource-make-resevation'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("operating hours", response.data["message"])

    def test_cancel_reservation_owner_success(self):
        from datetime import time, date
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="cancel_org@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        owner = User.objects.create_user(
            email="owner@example.com",
            password="userpassword123",
            first_name="Owner",
            last_name="User",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Pod")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Focus Pod",
            slot_interval=30,
            slot_start_time=time(9, 0),
            slot_end_time=time(17, 0),
        )
        reservation = Reservation.objects.create(
            user=owner,
            resource=resource,
            booking_date=date(2026, 11, 20),
            booking_slot_start_time=time(10, 0),
            booking_slot_end_time=time(10, 30),
            booking_status=Reservation.BOOKED,
        )

        self.client.force_authenticate(user=owner)
        payload = {"reservation_id": reservation.id}
        response = self.client.post(reverse('user-resource-cancel-reservation'), payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Reservation cancelled successfully")

        reservation.refresh_from_db()
        self.assertEqual(reservation.booking_status, Reservation.CANCELLED)

        # Confirm slot is freed up in get_slot
        slot_resp = self.client.get(
            reverse('user-resource-get-slot'),
            {'resource_id': resource.id, 'date': '2026-11-20'}
        )
        slot_10 = next(s for s in slot_resp.data["slots"] if s["start_time"] == "10:00:00")
        self.assertFalse(slot_10["is_booked"])

    def test_cancel_reservation_other_user_forbidden(self):
        from datetime import time, date
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="cancel_org2@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        owner = User.objects.create_user(
            email="owner2@example.com",
            password="userpassword123",
            first_name="Owner",
            last_name="Two",
            role=User.USER,
        )
        stranger = User.objects.create_user(
            email="stranger@example.com",
            password="userpassword123",
            first_name="Stranger",
            last_name="User",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Room")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Room 101",
            slot_interval=30,
            slot_start_time=time(9, 0),
            slot_end_time=time(17, 0),
        )
        reservation = Reservation.objects.create(
            user=owner,
            resource=resource,
            booking_date=date(2026, 11, 20),
            booking_slot_start_time=time(11, 0),
            booking_slot_end_time=time(11, 30),
            booking_status=Reservation.BOOKED,
        )

        # Stranger tries to cancel owner's reservation
        self.client.force_authenticate(user=stranger)
        payload = {"reservation_id": reservation.id}
        response = self.client.post(reverse('user-resource-cancel-reservation'), payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("not authorized", response.data["message"])

        reservation.refresh_from_db()
        self.assertEqual(reservation.booking_status, Reservation.BOOKED)

    def test_cancel_already_cancelled_reservation(self):
        from datetime import time, date
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="cancel_org3@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        owner = User.objects.create_user(
            email="owner3@example.com",
            password="userpassword123",
            first_name="Owner",
            last_name="Three",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Desk")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Hot Desk",
            slot_interval=30,
            slot_start_time=time(9, 0),
            slot_end_time=time(17, 0),
        )
        reservation = Reservation.objects.create(
            user=owner,
            resource=resource,
            booking_date=date(2026, 11, 20),
            booking_slot_start_time=time(12, 0),
            booking_slot_end_time=time(12, 30),
            booking_status=Reservation.CANCELLED,
        )

        self.client.force_authenticate(user=owner)
        payload = {"reservation_id": reservation.id}
        response = self.client.post(reverse('user-resource-cancel-reservation'), payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already cancelled", response.data["message"])

    def test_my_reservations_paginated(self):
        from datetime import time, date, timedelta
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="list_org@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        user = User.objects.create_user(
            email="list_user@example.com",
            password="userpassword123",
            first_name="List",
            last_name="User",
            role=User.USER,
        )
        other_user = User.objects.create_user(
            email="other_list_user@example.com",
            password="userpassword123",
            first_name="Other",
            last_name="User",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Conference")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Conf Room",
            slot_interval=30,
            slot_start_time=time(9, 0),
            slot_end_time=time(18, 0),
        )

        # Create 12 reservations for user
        base_date = date(2026, 12, 1)
        for i in range(12):
            Reservation.objects.create(
                user=user,
                resource=resource,
                booking_date=base_date + timedelta(days=i),
                booking_slot_start_time=time(10, 0),
                booking_slot_end_time=time(10, 30),
                booking_status=Reservation.BOOKED,
            )

        # Create 1 reservation for other_user (should NOT be in user's list)
        Reservation.objects.create(
            user=other_user,
            resource=resource,
            booking_date=base_date,
            booking_slot_start_time=time(11, 0),
            booking_slot_end_time=time(11, 30),
            booking_status=Reservation.BOOKED,
        )

        self.client.force_authenticate(user=user)

        # Page 1 (default page_size 10)
        response = self.client.get(reverse('user-resource-user-reservations'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 12)
        self.assertEqual(len(response.data["results"]), 10)
        self.assertIsNotNone(response.data["next"])

        # Page 2
        response_p2 = self.client.get(reverse('user-resource-user-reservations'), {'page': 2})
        self.assertEqual(response_p2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_p2.data["results"]), 2)

    def test_my_reservations_status_filter(self):
        from datetime import time, date
        from resourses.models import ResourseCategory, Resource, Reservation

        org = User.objects.create_user(
            email="filter_org@example.com",
            password="orgpassword123",
            role=User.ORGANISATION,
        )
        user = User.objects.create_user(
            email="filter_user@example.com",
            password="userpassword123",
            first_name="Filter",
            last_name="User",
            role=User.USER,
        )
        cat = ResourseCategory.objects.create(name="Lab Space")
        resource = Resource.objects.create(
            organisation=org,
            category=cat,
            title="Lab Space 1",
            slot_interval=60,
            slot_start_time=time(9, 0),
            slot_end_time=time(17, 0),
        )

        # 1 booked, 1 cancelled
        Reservation.objects.create(
            user=user,
            resource=resource,
            booking_date=date(2026, 12, 1),
            booking_slot_start_time=time(9, 0),
            booking_slot_end_time=time(10, 0),
            booking_status=Reservation.BOOKED,
        )
        Reservation.objects.create(
            user=user,
            resource=resource,
            booking_date=date(2026, 12, 2),
            booking_slot_start_time=time(10, 0),
            booking_slot_end_time=time(11, 0),
            booking_status=Reservation.CANCELLED,
        )

        self.client.force_authenticate(user=user)

        # Filter booked
        resp_booked = self.client.get(reverse('user-resource-user-reservations'), {'status': 'booked'})
        self.assertEqual(resp_booked.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_booked.data["count"], 1)
        self.assertEqual(resp_booked.data["results"][0]["booking_status"], "booked")

        # Filter cancelled
        resp_cancelled = self.client.get(reverse('user-resource-user-reservations'), {'status': 'cancelled'})
        self.assertEqual(resp_cancelled.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_cancelled.data["count"], 1)
        self.assertEqual(resp_cancelled.data["results"][0]["booking_status"], "cancelled")
