from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from .models import Asset, User, Allocation
from .forms import AssetForm, UserForm, AllocationForm, DeallocationForm
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from chartjs.views.lines import BaseLineChartView
from django.contrib.admin.views.decorators import staff_member_required

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
            Q(asset_type__icontains=search_query) |
            Q(asset_number__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(room_number__icontains=search_query) |
            Q(purchase_date__icontains=search_query) |
            Q(depreciation_date__icontains=search_query)
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
            try:
                form.save()
                messages.success(request, 'Asset created successfully.')
                return redirect('asset_list')
            except Exception as e:
                messages.error(request, f'Error creating asset: {str(e)}')
    else:
        form = AssetForm()
    return render(request, 'assets/asset_form.html', {'form': form})

@staff_member_required
def asset_update(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, 'Asset updated successfully.')
            return redirect('asset_detail', pk=pk)
    else:
        form = AssetForm(instance=asset)
    return render(request, 'assets/asset_form.html', {'form': form, 'asset': asset})

@staff_member_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted successfully.')
        return redirect('asset_list')
    return render(request, 'assets/asset_confirm_delete.html', {'asset': asset})

@staff_member_required
def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('user_list')
    return render(request, 'assets/user_confirm_delete.html', {'user': user})


def user_list(request):
    search_query = request.GET.get('search', '')
    users = User.objects.all()
    if search_query:
        users = users.filter(name__icontains=search_query)
    return render(request, 'assets/user_list.html', {'users': users, 'search_query': search_query})


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