import csv
import io
from .models import User
from django.db import IntegrityError
from .forms import CSVUploadForm
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Count
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from rest_framework import viewsets
from .serializers import AssetSerializer, AssetTypeSerializer, LocationSerializer, RoomNumberSerializer, UserSerializer
from .models import Asset, AssetType, Location, RoomNumber, User, Department, Allocation
from chartjs.views.lines import BaseLineChartView
from .models import Asset, User, Allocation, AssetType, Location, RoomNumber
from .forms import AssetForm, UserForm, AllocationForm, DeallocationForm, AssetTypeForm, LocationForm, RoomNumberForm, DepartmentForm

class AssetAllocationChart(BaseLineChartView):
    def get_labels(self):
        return [asset.asset_type for asset in Asset.objects.values('asset_type').distinct()]

    def get_data(self):
        asset_types = self.get_labels()
        return [
            [Asset.objects.filter(asset_type=asset_type, is_allocated=True).count() for asset_type in asset_types],
            [Asset.objects.filter(asset_type=asset_type, is_allocated=False).count() for asset_type in asset_types],
        ]

    def get_colors(self):
        return [
            'rgba(75, 192, 192, 0.6)',
            'rgba(255, 99, 132, 0.6)',
        ]

def dashboard(request):
    asset_count = Asset.objects.count()
    user_count = User.objects.count()
    allocation_count = Allocation.objects.count()
    recent_allocations = Allocation.objects.order_by('-assigned_date')[:5]
    
    asset_types = Asset.objects.values('asset_type').annotate(count=Count('asset_type'))
    
    context = {
        'asset_count': asset_count,
        'user_count': user_count,
        'allocation_count': allocation_count,
        'recent_allocations': recent_allocations,
        'asset_types': asset_types,
    }
    return render(request, 'assets/dashboard.html', context)

def admin_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'assets/admin_login.html', {'error': 'Invalid credentials or not an admin user'})
    return render(request, 'assets/admin_login.html')

def asset_list(request):
    search_query = request.GET.get('search', '')
    assets = Asset.objects.all()
    if search_query:
        assets = assets.filter(
            Q(asset_type__name__icontains=search_query) |
            Q(asset_number__icontains=search_query) |
            Q(location__name__icontains=search_query) |
            Q(room_number__number__icontains=search_query) |
            Q(purchase_date__icontains=search_query) |
            Q(depreciation_date__icontains=search_query)|
            Q(department__name__icontains=search_query)
        )
    return render(request, 'assets/asset_list.html', {'assets': assets, 'search_query': search_query})

def asset_detail(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    return render(request, 'assets/asset_detail.html', {'asset': asset})

@staff_member_required
def asset_create(request):
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.save()  # This will trigger the custom save method to set depreciation_date and current_value
            messages.success(request, 'Asset created successfully.')
            return redirect('asset_detail', pk=asset.pk)
    else:
        form = AssetForm()
    
    context = {
        'form': form,
        'asset_type_form': AssetTypeForm(),
        'location_form': LocationForm(),
        'room_number_form': RoomNumberForm(),
        'department_form': DepartmentForm(),
    }
    return render(request, 'assets/asset_form.html', context)

@staff_member_required
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.save()  # This will trigger the custom save method to update depreciation_date and current_value
            messages.success(request, 'Asset updated successfully.')
            return redirect('asset_detail', pk=pk)
    else:
        form = AssetForm(instance=asset)
    
    context = {
        'form': form,
        'asset': asset,
        'asset_type_form': AssetTypeForm(),
        'location_form': LocationForm(),
        'room_number_form': RoomNumberForm(),
        'department_form': DepartmentForm(),
    }
    return render(request, 'assets/asset_form.html', context)

@staff_member_required
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            department = form.save()
            return JsonResponse({'id': department.id, 'name': department.name})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted successfully.')
        return redirect('asset_list')
    return render(request, 'assets/asset_confirm_delete.html', {'asset': asset})

def user_list(request):
    search_query = request.GET.get('search', '')
    users = User.objects.all()
    if search_query:
        users = users.filter(Q(name__icontains=search_query) | Q(email__icontains=search_query))
    
    upload_form = CSVUploadForm()
    
    context = {
        'users': users, 
        'search_query': search_query,
        'upload_form': upload_form,
        'is_staff': request.user.is_staff  # Pass this flag to the template
    }
    
    return render(request, 'assets/user_list.html', context)

@staff_member_required
def import_users_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    user, created = User.objects.update_or_create(
                        email=row['email'],
                        defaults={'name': row['name']}
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
                except IntegrityError:
                    error_count += 1
            
            messages.success(request, f'Import complete. {created_count} users created, {updated_count} users updated, {error_count} errors.')
        else:
            messages.error(request, 'Invalid form submission.')
    return redirect('user_list')

def user_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    allocations = Allocation.objects.filter(user=user)
    return render(request, 'assets/user_detail.html', {'user': user, 'allocations': allocations})

@staff_member_required
def user_create(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'User created successfully.')
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'assets/user_form.html', {'form': form})

@staff_member_required
def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'User updated successfully.')
            return redirect('user_detail', pk=pk)
    else:
        form = UserForm(instance=user)
    return render(request, 'assets/user_form.html', {'form': form, 'user': user})

@staff_member_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('user_list')
    return render(request, 'assets/user_confirm_delete.html', {'user': user})

@staff_member_required
def allocate_asset(request):
    if request.method == 'POST':
        form = AllocationForm(request.POST)
        if form.is_valid():
            allocation = form.save()
            allocation.asset.is_allocated = True
            allocation.asset.save()
            messages.success(request, 'Asset allocated successfully.')
            return redirect('asset_detail', pk=allocation.asset.pk)
    else:
        form = AllocationForm()
    return render(request, 'assets/allocation_form.html', {'form': form})

@staff_member_required
def deallocate_asset(request, pk):
    allocation = get_object_or_404(Allocation, pk=pk)
    if request.method == 'POST':
        form = DeallocationForm(request.POST)
        if form.is_valid():
            allocation.return_date = form.cleaned_data['return_date']
            allocation.asset.is_allocated = False
            allocation.asset.save()
            allocation.save()
            messages.success(request, 'Asset deallocated successfully.')
            return redirect('asset_detail', pk=allocation.asset.pk)
    else:
        form = DeallocationForm(initial={'return_date': timezone.now().date()})
    return render(request, 'assets/deallocation_form.html', {'form': form, 'allocation': allocation})

def allocation_list(request):
    allocations = Allocation.objects.filter(return_date__isnull=True)
    return render(request, 'assets/allocation_list.html', {'allocations': allocations})

@staff_member_required
def add_asset_type(request):
    if request.method == 'POST':
        form = AssetTypeForm(request.POST)
        if form.is_valid():
            asset_type = form.save()
            return JsonResponse({'id': asset_type.id, 'name': asset_type.name})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def add_location(request):
    if request.method == 'POST':
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            return JsonResponse({'id': location.id, 'name': location.name})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@staff_member_required
def add_room_number(request):
    if request.method == 'POST':
        form = RoomNumberForm(request.POST)
        if form.is_valid():
            room_number = form.save()
            return JsonResponse({'id': room_number.id, 'number': room_number.number})
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_users(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(name__icontains=query)[:10]
    return JsonResponse({'results': [{'id': user.id, 'text': user.name} for user in users]})

class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer

class AssetTypeViewSet(viewsets.ModelViewSet):
    queryset = AssetType.objects.all()
    serializer_class = AssetTypeSerializer

class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer

class RoomNumberViewSet(viewsets.ModelViewSet):
    queryset = RoomNumber.objects.all()
    serializer_class = RoomNumberSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer