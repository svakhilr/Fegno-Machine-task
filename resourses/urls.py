from django.urls import path
from resourses.views import ResourseCategoryCreateView, ResourceCreateView

urlpatterns = [
    # Category endpoints
    path('categories/', ResourseCategoryCreateView.as_view(), name='category-list-create'),
    path('category/create/', ResourseCategoryCreateView.as_view(), name='category-create'),

    # Resource endpoints
    path('', ResourceCreateView.as_view(), name='resource-list-create'),
    path('create/', ResourceCreateView.as_view(), name='resource-create'),
]
