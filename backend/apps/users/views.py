# backend/apps/users/views.py
# Vistas del módulo de usuarios.
# Cada función maneja una URL y devuelve una respuesta HTTP.

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from apps.sales.models import Sale
from apps.patients.models import Patient
from apps.bonuses.models import Bonus
from django.utils import timezone


def login_view(request):
    # Si el usuario ya está autenticado, lo mandamos al inicio
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        # Recogemos los datos del formulario
        email = request.POST.get('email')
        password = request.POST.get('password')

        # authenticate() comprueba si el email y contraseña son correctos
        # Devuelve el objeto User si son válidos, o None si no
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # login() crea la sesión del usuario en el navegador
            login(request, user)
            # Redirigimos al inicio (más adelante será el dashboard)
            return redirect('/')
        else:
            # Si las credenciales son incorrectas, mostramos un error
            messages.error(request, 'Email o contraseña incorrectos.')

    # GET: mostramos el formulario vacío
    # POST fallido: mostramos el formulario con el mensaje de error
    return render(request, 'users/login.html')


def logout_view(request):
    # logout() elimina la sesión del usuario
    logout(request)
    return redirect('users:login')


@login_required  # este decorador redirige a LOGIN_URL si el usuario no está autenticado
def profile_view(request):
    # Por ahora solo mostramos la página de perfil
    # En el siguiente paso añadiremos el formulario de edición
    return render(request, 'users/profile.html')


@login_required
def dashboard_view(request):
    """
    Página de inicio — muestra un resumen general de la clínica.
    """
    # Mes y año actuales para filtrar
    today = timezone.localdate()
    current_month = today.month
    current_year = today.year

    # --- VENTAS DEL MES ACTUAL ---
    sales_this_month = Sale.objects.filter(
        date__month=current_month,
        date__year=current_year
    )

    # Total facturado este mes
    total_month = sales_this_month.aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Número de ventas este mes
    count_month = sales_this_month.count()

    # --- ÚLTIMAS 5 VENTAS ---
    latest_sales = Sale.objects.select_related(
        'patient', 'worker'
    ).order_by('-date', '-created_at')[:5]

    # --- ESTADÍSTICAS GENERALES ---
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