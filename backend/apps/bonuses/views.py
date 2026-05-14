# backend/apps/bonuses/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from apps.patients.models import Patient
from .models import Bonus
from .forms import BonusForm
import unicodedata


def normalizar(texto):
    # NFD separa caracteres de sus tildes, ascii las elimina: "García" → "garcia"
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()


@login_required
def bonus_list(request):
    query = request.GET.get('q', '')
    bonuses = Bonus.objects.select_related('patient').order_by('-bonus_number')

    if query:
        query_normalizado = normalizar(query)
        bonuses = [
            b for b in bonuses
            if query_normalizado in normalizar(b.patient.first_name)
            or query_normalizado in normalizar(b.patient.last_name)
            or query_normalizado in b.bonus_number.lower()
        ]

    paginator = Paginator(bonuses, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'bonuses/list.html', {
        'bonuses': page_obj,
        'query': query,
        'page_obj': page_obj,
    })


@login_required
def bonus_detail(request, pk):
    bonus = get_object_or_404(Bonus, pk=pk)
    return render(request, 'bonuses/detail.html', {'bonus': bonus})


@login_required
def bonus_create(request):
    if request.method == 'POST':
        form = BonusForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('bonuses:list')
    else:
        form = BonusForm()

    return render(request, 'bonuses/form.html', {
        'form': form,
        'title': 'Nuevo bono',
    })


@login_required
def search_patients(request):
    """
    Vista HTMX — devuelve un fragmento HTML con pacientes que coinciden con la búsqueda.
    Se llama mientras el usuario escribe, sin recargar la página.
    """
    query = request.GET.get('q', '').strip()

    if len(query) >= 2:
        # Mínimo 2 caracteres para no disparar búsquedas con cada tecla
        # Filtramos en Python porque PostgreSQL no normaliza tildes por defecto
        query_normalizado = normalizar(query)
        patients = [
            p for p in Patient.objects.filter(is_active=True).order_by('last_name', 'first_name')
            if query_normalizado in normalizar(p.first_name)
            or query_normalizado in normalizar(p.last_name)
        ][:10]
    else:
        patients = Patient.objects.none()

    # Devolvemos solo el fragmento HTML — HTMX lo inyecta en el DOM sin recargar
    return render(request, 'bonuses/partials/patient_results.html', {
        'patients': patients,
        'query': query,
    })