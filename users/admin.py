from django.contrib import admin
from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'first_name', 'last_name', 'organisation_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name', 'organisation_name')
