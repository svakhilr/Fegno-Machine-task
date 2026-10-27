from django.db.models.signals import ModelSignal
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from users.manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    ORGANISATION = 'organisation'
    USER = 'user'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (ORGANISATION, 'Organisation'),
        (USER, 'User'),
        (ADMIN, 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=USER)
    organisation_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, null=False, blank=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email