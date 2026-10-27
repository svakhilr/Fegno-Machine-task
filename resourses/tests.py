from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from resourses.models import ResourseCategory, Resource


class ResourseAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Organisation user
        self.org_user = User.objects.create_user(
            email="org@company.com",
            password="orgpassword123",
            organisation_name="Tech Solutions",
            role=User.ORGANISATION,
        )

        # Regular user
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="userpassword123",
            first_name="Jane",
            last_name="Doe",
            role=User.USER,
        )

        # Initial category
        self.category = ResourseCategory.objects.create(name="Conference Room")

    def test_create_category_authenticated(self):
        self.client.force_authenticate(user=self.org_user)
        data = {"name": "Meeting Room"}
        response = self.client.post(reverse('category-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["name"], "Meeting Room")
        self.assertTrue(ResourseCategory.objects.filter(name="Meeting Room").exists())

    def test_create_category_unauthenticated(self):
        data = {"name": "Auditorium"}
        response = self.client.post(reverse('category-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_categories(self):
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(reverse('category-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

    def test_create_resource_by_organisation_success(self):
        self.client.force_authenticate(user=self.org_user)
        data = {
            "category": self.category.id,
            "title": "Main Boardroom",
            "slot_interval": 30,
            "slot_start_time": "09:00:00",
            "slot_end_time": "17:00:00",
        }
        response = self.client.post(reverse('resource-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["title"], "Main Boardroom")
        self.assertEqual(response.data["data"]["organisation"], self.org_user.id)
        self.assertTrue(Resource.objects.filter(title="Main Boardroom").exists())

    def test_create_resource_by_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.regular_user)
        data = {
            "category": self.category.id,
            "title": "Desk 101",
            "slot_interval": 60,
            "slot_start_time": "09:00:00",
            "slot_end_time": "18:00:00",
        }
        response = self.client.post(reverse('resource-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_resource_invalid_time_range(self):
        self.client.force_authenticate(user=self.org_user)
        data = {
            "category": self.category.id,
            "title": "Invalid Room",
            "slot_interval": 30,
            "slot_start_time": "18:00:00",
            "slot_end_time": "09:00:00",  # end before start
        }
        response = self.client.post(reverse('resource-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slot_end_time", response.data)

    def test_create_resource_invalid_slot_interval(self):
        self.client.force_authenticate(user=self.org_user)
        data = {
            "category": self.category.id,
            "title": "Invalid Interval Room",
            "slot_interval": 0,
            "slot_start_time": "09:00:00",
            "slot_end_time": "17:00:00",
        }
        response = self.client.post(reverse('resource-list-create'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("slot_interval", response.data)

    def test_list_resources(self):
        Resource.objects.create(
            organisation=self.org_user,
            category=self.category,
            title="Room A",
            slot_interval=15,
            slot_start_time="10:00:00",
            slot_end_time="12:00:00",
        )
        self.client.force_authenticate(user=self.org_user)
        response = self.client.get(reverse('resource-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)
