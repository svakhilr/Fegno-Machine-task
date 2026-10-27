from rest_framework import serializers
from resourses.models import ResourseCategory, Resource
from users.models import User


class ResourseCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourseCategory
        fields = ('id', 'name', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_name(self, value):
        name = value.strip()
        if not name:
            raise serializers.ValidationError("Category name cannot be empty.")
        if ResourseCategory.objects.filter(name__iexact=name).exists():
            raise serializers.ValidationError("A category with this name already exists.")
        return name


class OrganisationResourceListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Resource
        fields = ('id', 'category_name', 'title', 'slot_interval', 'slot_start_time', 'slot_end_time', 'is_active')


class ResourceSerializer(serializers.ModelSerializer):
    organisation = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        required=False
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=ResourseCategory.objects.all()
    )

    class Meta:
        model = Resource
        fields = (
            'id',
            'organisation',
            'category',
            'title',
            'slot_interval',
            'slot_start_time',
            'slot_end_time',
            'is_active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_slot_interval(self, value):
        if value <= 0:
            raise serializers.ValidationError("Slot interval must be greater than 0.")
        return value

    def validate(self, attrs):
        start = attrs.get('slot_start_time')
        end = attrs.get('slot_end_time')

        if start and end and start >= end:
            raise serializers.ValidationError({
                "slot_end_time": "slot_end_time must be after slot_start_time."
            })

        request = self.context.get('request')
        organisation = attrs.get('organisation')

        # Auto-assign organisation from authenticated user if not explicitly passed
        if not organisation:
            if request and request.user and request.user.is_authenticated:
                if request.user.role in [User.ORGANISATION, User.ADMIN] or request.user.is_staff or request.user.is_superuser:
                    attrs['organisation'] = request.user
                else:
                    raise serializers.ValidationError({
                        "organisation": "Only users with organisation or admin role can create resources."
                    })
            else:
                raise serializers.ValidationError({
                    "organisation": "Organisation is required."
                })
        else:
            if organisation.role not in [User.ORGANISATION, User.ADMIN] and not organisation.is_staff:
                raise serializers.ValidationError({
                    "organisation": "Selected user is not an organisation."
                })

        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['category_name'] = instance.category.name if instance.category else None
        data['organisation_email'] = instance.organisation.email if instance.organisation else None
        data['organisation_name'] = instance.organisation.organisation_name if instance.organisation else None
        return data


class ResourseListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name', read_only=True)
    organisation = serializers.CharField(source='organisation.organisation_name', read_only=True)
    class Meta:
        model = Resource
        fields = ('id','title','organisation')


class ReservationSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    resource_title = serializers.CharField(source='resource.title', read_only=True)
    organisation_name = serializers.CharField(source='resource.organisation.organisation_name', read_only=True)
    category_name = serializers.CharField(source='resource.category.name', read_only=True)

    class Meta:
        from resourses.models import Reservation
        model = Reservation
        fields = (
            'id',
            'user',
            'user_email',
            'resource',
            'resource_title',
            'organisation_name',
            'category_name',
            'booking_status',
            'booking_date',
            'booking_slot_start_time',
            'booking_slot_end_time',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
