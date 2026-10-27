from django.contrib import admin
from resourses.models import ResourseCategory, Resource, Reservation


@admin.register(ResourseCategory)
class ResourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'organisation', 'category', 'slot_interval', 'slot_start_time', 'slot_end_time', 'is_active')
    list_filter = ('is_active', 'category', 'organisation')
    search_fields = ('title', 'organisation__email')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'resource', 'booking_status', 'booking_date', 'booking_slot_start_time', 'booking_slot_end_time')
    list_filter = ('booking_status', 'booking_date')
    search_fields = ('user__email', 'resource__title')
