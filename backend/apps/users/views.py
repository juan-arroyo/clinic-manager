# backend/apps/users/views.py

from functools import wraps
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum
from apps.sales.models import Sale
from apps.patients.models import Patient
from apps.bonuses.models import Bonus




def staff_required(view_func):
    """
    Decorador para vistas de escritura — solo accesible por is_staff=True.
    Redirige al login si no está autenticado, devuelve 403 si no es staff.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_staff:
            return HttpResponseForbidden(
                render(request, '403.html').content
            )
        return view_func(request, *args, **kwargs)
    return wrapper

def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        # authenticate() devuelve el User si las credenciales son válidas, o None
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Email o contraseña incorrectos.')

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    return redirect('users:login')


@login_required
def profile_view(request):
    return render(request, 'users/profile.html')


@login_required
def dashboard_view(request):
    today = timezone.localdate()
    current_month = today.month
    current_year = today.year

    # --- VENTAS DEL MES ACTUAL ---
    sales_this_month = Sale.objects.filter(
        date__month=current_month,
        date__year=current_year
    )
    total_month = sales_this_month.aggregate(total=Sum('amount'))['total'] or 0
    count_month = sales_this_month.count()

    # --- ÚLTIMAS 5 VENTAS ---
    latest_sales = Sale.objects.select_related(
        'patient', 'worker'
    ).order_by('-date', '-created_at')[:5]

    # --- TOTALES GENERALES ---
    total_patients = Patient.objects.filter(is_active=True).count()
    total_active_bonuses = Bonus.objects.filter(is_active=True).count()

    return render(request, 'users/dashboard.html', {
        'total_month': total_month,
        'count_month': count_month,
        'latest_sales': latest_sales,
        'total_patients': total_patients,
        'total_active_bonuses': total_active_bonuses,
        'today': today,
    })