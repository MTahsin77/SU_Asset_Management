import csv
import io
import json
from django.core.management import call_command
from django.contrib.auth.views import LogoutView
from django.views.decorators.http import require_http_methods
import tempfile
import os
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from decimal import Decimal
from datetime import datetime, timedelta
from .models import User
from django.db import IntegrityError
from .forms import CSVUploadForm
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.db.models import Q, Count, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from rest_framework import viewsets
from .serializers import AssetSerializer, AssetTypeSerializer, LocationSerializer, RoomNumberSerializer, UserSerializer
from .models import Asset, AssetType, Location, RoomNumber, User, Department, Allocation
from chartjs.views.lines import BaseLineChartView
from .models import Asset, User, Allocation, AssetType, Location, RoomNumber, Department
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
    # Asset counts
    total_assets = Asset.objects.count()
    allocated_assets = Asset.objects.filter(assigned_to__isnull=False).count()
    unallocated_assets = total_assets - allocated_assets

    # Asset allocation by type
    asset_types = AssetType.objects.annotate(
        total=Count('asset'),
        allocated=Count('asset', filter=models.Q(asset__assigned_to__isnull=False))
    )

    # Asset value over time
    now = timezone.now()
    years = 5
    value_over_time = []
    for i in range(years):
        date = now - timedelta(days=365 * i)
        total_value = Asset.objects.filter(purchase_date__lte=date).aggregate(
            total=Sum('current_value'))['total'] or 0
        value_over_time.append({'date': date.strftime('%Y-%m-%d'), 'value': total_value})
    
    # Top departments by asset count
    top_departments = Department.objects.annotate(
        asset_count=Count('asset')).order_by('-asset_count')[:5]

    # Recent acquisitions
    recent_acquisitions = Asset.objects.order_by('-purchase_date')[:10]

    # Depreciation summary
    total_purchase_value = Asset.objects.aggregate(total=Sum('purchase_value'))['total'] or 0
    total_current_value = Asset.objects.aggregate(total=Sum('current_value'))['total'] or 0
    total_depreciation = total_purchase_value - total_current_value

    context = {
        'total_assets': total_assets,
        'allocated_assets': allocated_assets,
        'unallocated_assets': unallocated_assets,
        'asset_types': asset_types,
        'value_over_time': value_over_time,
        'top_departments': top_departments,
        'recent_acquisitions': recent_acquisitions,
        'total_purchase_value': total_purchase_value,
        'total_current_value': total_current_value,
        'total_depreciation': total_depreciation,
        'asset_types_json': json.dumps(list(asset_types.values('name', 'total', 'allocated')), cls=DjangoJSONEncoder),
        'value_over_time_json': json.dumps(value_over_time, cls=DjangoJSONEncoder),
        'top_departments_json': json.dumps(list(top_departments.values('name', 'asset_count')), cls=DjangoJSONEncoder),
        'depreciation_data': json.dumps({
            'currentValue': float(total_current_value),
            'depreciation': float(total_depreciation)
        }, cls=DjangoJSONEncoder),
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
    assets = Asset.objects.all()
    asset_types = AssetType.objects.all()
    locations = Location.objects.all()
    departments = Department.objects.all()
    users = User.objects.all()

    # Filter by asset type
    asset_type_id = request.GET.get('asset_type')
    if asset_type_id:
        assets = assets.filter(asset_type_id=asset_type_id)

    # Filter by location
    location_id = request.GET.get('location')
    if location_id:
        assets = assets.filter(location_id=location_id)

    # Filter by department
    department_id = request.GET.get('department')
    if department_id:
        assets = assets.filter(department_id=department_id)

    # Filter by allocated user
    user_id = request.GET.get('allocated_to')
    if user_id:
        if user_id == 'unallocated':
            assets = assets.filter(assigned_to__isnull=True)
        else:
            assets = assets.filter(assigned_to_id=user_id)

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        assets = assets.filter(
            Q(asset_number__icontains=search_query) |
            Q(asset_type__name__icontains=search_query) |
            Q(assigned_to__name__icontains=search_query)
        )

    context = {
        'assets': assets,
        'asset_types': asset_types,
        'locations': locations,
        'departments': departments,
        'users': users,
        'search_query': search_query,
        'selected_asset_type': asset_type_id,
        'selected_location': location_id,
        'selected_department': department_id,
        'selected_user': user_id,
    }
    return render(request, 'assets/asset_list.html', context)

def export_assets(request):
    assets = Asset.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="assets.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Asset Number', 'Location', 'Department', 'Room Number', 'Purchase Date', 
                     'Purchase Value', 'Current Value', 'Assigned To', 'Is Allocated', 'Sticker Deployed'])
    
    for asset in assets:
        writer.writerow([
            asset.asset_number,
            asset.location.name if asset.location else '',
            asset.department.name if asset.department else '',
            asset.room_number.number if asset.room_number else '',
            asset.purchase_date,
            asset.purchase_value,
            asset.current_value,
            asset.assigned_to.name if asset.assigned_to else '',
            asset.is_allocated,
            asset.sticker_deployed
        ])
    
    return response


def truncate(value, max_length=255):
    return (value[:max_length] if value else None)

@staff_member_required
def import_assets(request):
    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)
        
        for row in reader:
            # Create or get AssetType (using 'model' as asset_type)
            asset_type, _ = AssetType.objects.get_or_create(name=row['model'])
            
            # Create or get Location
            location, _ = Location.objects.get_or_create(name=row['location'] if row['location'] else 'Unknown')
            
            # Create or get RoomNumber
            room_number, _ = RoomNumber.objects.get_or_create(number=row['room_number'] if row['room_number'] else 'Unknown')
            
            # Create or get Department
            department, _ = Department.objects.get_or_create(name=row['department'] if row['department'] else 'Unknown')
            
            # Create or get User
            user = None
            if row['assigned_to']:
                user, _ = User.objects.get_or_create(
                    name=row['assigned_to'],
                    defaults={'email': row.get('email', '')}
                )
            
            # Parse purchase date
            purchase_date = None
            if row['purchase_date']:
                try:
                    purchase_date = datetime.strptime(row['purchase_date'], '%Y-%m-%d').date()
                except ValueError:
                    messages.warning(request, f"Invalid purchase date for asset {row['asset_number']}. Left as Unknown.")
            
            # Create or update Asset
            asset, created = Asset.objects.update_or_create(
                asset_number=row['asset_number'],
                defaults={
                    'asset_type': asset_type,
                    'location': location,
                    'room_number': room_number,
                    'department': department,
                    'purchase_date': purchase_date,
                    'purchase_value': Decimal(row['purchase_value']) if row['purchase_value'] else None,
                    'current_value': Decimal(row['current_value']) if row['current_value'] else None,
                    'is_allocated': bool(user),
                    'assigned_to': user,
                    'sticker_deployed': row['sticker_deployed'].lower() == 'true' if row['sticker_deployed'] else False
                }
            )
            
            # Create Allocation if user is assigned
            if user:
                Allocation.objects.update_or_create(
                    asset=asset,
                    defaults={
                        'user': user,
                        'assigned_date': datetime.now().date(),
                        'return_date': None
                    }
                )
        
        messages.success(request, 'CSV imported successfully. Assets, Users, and Allocations have been created/updated.')
    else:
        messages.error(request, 'Please upload a CSV file.')
    
    return redirect('asset_list')



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
                        name=row['name'],  # Use name as the key
                        defaults={'email': row.get('email', '')}  # Email is optional
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
    allocated_assets = Asset.objects.filter(assigned_to=user)
    context = {
        'user': user,
        'assets': allocated_assets,
    }
    return render(request, 'assets/user_detail.html', context)

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
@require_POST
@csrf_exempt
def allocate_asset(request):
    data = json.loads(request.body)
    asset_id = data.get('asset_id')
    user_id = data.get('user_id')
    assigned_date = data.get('assigned_date')

    try:
        asset = Asset.objects.get(id=asset_id)
        user = User.objects.get(id=user_id)
        
        allocation, created = Allocation.objects.update_or_create(
            asset=asset,
            defaults={'user': user, 'assigned_date': assigned_date}
        )
        
        asset.is_allocated = True
        asset.save()

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

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
    form = AssetTypeForm(request.POST)
    if form.is_valid():
        asset_type = form.save()
        return JsonResponse({'id': asset_type.id, 'name': asset_type.name})
    else:
        return JsonResponse({'error': form.errors.as_json()}, status=400)

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

class AssetAllocationChart(BaseLineChartView):
    def get_labels(self):
        return [asset.asset_type for asset in Asset.objects.values('asset_type').distinct()]

    def get_data(self):
        asset_types = self.get_labels()
        return [
            [Asset.objects.filter(asset_type=asset_type, is_allocated=True).count() for asset_type in asset_types],
            [Asset.objects.filter(asset_type=asset_type, is_allocated=False).count() for asset_type in asset_types],
        ]