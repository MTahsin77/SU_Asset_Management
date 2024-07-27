from django.urls import path, include
from . import views
from .views import AssetAllocationChart
from .views import admin_login
from django.contrib.auth.views import LogoutView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'assets', views.AssetViewSet)
router.register(r'asset-types', views.AssetTypeViewSet)
router.register(r'locations', views.LocationViewSet)
router.register(r'room-numbers', views.RoomNumberViewSet)
router.register(r'users', views.UserViewSet)


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('add-department/', views.add_department, name='add_department'),
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/update/', views.asset_update, name='asset_update'),
    path('users/', views.user_list, name='user_list'),
    path('users/import-csv/', views.import_users_csv, name='import_users_csv'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('allocate/', views.allocate_asset, name='allocate_asset'),
    path('chart/asset-allocation/', AssetAllocationChart.as_view(), name='asset_allocation_chart'),
    path('deallocate/<int:pk>/', views.deallocate_asset, name='deallocate_asset'),
    path('allocations/', views.allocation_list, name='allocation_list'),
    path('admin-login/', admin_login, name='admin_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api/', include(router.urls)),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
    path('add-asset-type/', views.add_asset_type, name='add_asset_type'),
    path('add-location/', views.add_location, name='add_location'),
    path('add-room-number/', views.add_room_number, name='add_room_number'),
    path('get-users/', views.get_users, name='get_users'),
]
