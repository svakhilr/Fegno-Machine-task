from rest_framework import serializers
from django.contrib.auth import authenticate
from users.models import User


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'password')
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=User.USER,
        )


class OrganisationRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6, style={'input_type': 'password'})
    organisation_name = serializers.CharField(required=False, allow_blank=True, max_length=100)

    class Meta:
        model = User
        fields = ('id', 'email', 'password', 'organisation_name')
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
        }

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("An organisation with this email already exists.")
        return normalized

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            organisation_name=validated_data.get('organisation_name', ''),
            first_name='',
            last_name='',
            role=User.ORGANISATION,
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    role = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        password = attrs.get('password')
        expected_role = attrs.get('role')

        if not email or not password:
            raise serializers.ValidationError("Both email and password are required.")

        user = authenticate(request=self.context.get('request'), email=email, password=password)
        if not user:
            user = authenticate(request=self.context.get('request'), username=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is inactive.")

        if expected_role and user.role != expected_role:
            raise serializers.ValidationError(f"Invalid account type. This account is registered as a '{user.role}'.")

        attrs['user'] = user
        return attrs


class UserResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'organisation_name', 'role', 'is_active')
