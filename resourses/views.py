from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from resourses.models import ResourseCategory, Resource
from resourses.serializers import ResourseCategorySerializer, ResourceSerializer,OrganisationResourceListSerializer
from resourses.permissions import IsOrganisation
from users.models import User


class ResourseCategoryCreateView(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = ResourseCategory.objects.filter(is_active=True).order_by('-created_at')
        serializer = ResourseCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ResourseCategorySerializer(data=request.data)
        if serializer.is_valid():
            category = serializer.save()
            return Response(
                {
                    "message": "Resource category created successfully",
                    "data": ResourseCategorySerializer(category).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResourceCreateView(APIView):
    """
    API endpoint for listing and creating Resources.
    GET: List resources.
    POST: Create a new resource (Requires organisation or admin role).
    """
    permission_classes = [IsAuthenticated, IsOrganisation]

    def get(self, request):
        if request.user.role == User.ORGANISATION:
            resources = Resource.objects.filter(organisation=request.user).order_by('-created_at')
        

        serializer = OrganisationResourceListSerializer(resources, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ResourceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            resource = serializer.save()
            return Response(
                {
                    "message": "Resource created successfully",
                    "data": ResourceSerializer(resource).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
