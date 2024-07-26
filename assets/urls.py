from django.urls import path
from . import views
from .views import AssetAllocationChart
from .views import admin_login
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('assets/', views.asset_list, name='asset_list'),
    path('assets/<int:pk>/', views.asset_detail, name='asset_detail'),
    path('assets/create/', views.asset_create, name='asset_create'),
    path('assets/<int:pk>/update/', views.asset_update, name='asset_update'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:pk>/update/', views.user_update, name='user_update'),
    path('allocate/', views.allocate_asset, name='allocate_asset'),
    path('chart/asset-allocation/', AssetAllocationChart.as_view(), name='asset_allocation_chart'),
    path('deallocate/<int:pk>/', views.deallocate_asset, name='deallocate_asset'),
    path('allocations/', views.allocation_list, name='allocation_list'),
    path('admin-login/', admin_login, name='admin_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('assets/<int:pk>/delete/', views.asset_delete, name='asset_delete'),
    path('users/<int:pk>/delete/', views.user_delete, name='user_delete'),
]
