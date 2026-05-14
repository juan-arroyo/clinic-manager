# backend/apps/patients/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Patient
from .forms import PatientForm
import unicodedata


def normalizar(texto):
    # NFD separa caracteres de sus tildes, ascii las elimina: "García" → "garcia"
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()


@login_required
def patient_list(request):
    query = request.GET.get('q', '')
    patients = Patient.objects.filter(is_active=True).order_by('last_name', 'first_name')

    if query:
        # Filtramos en Python en lugar de usar icontains de Django
        # porque PostgreSQL no normaliza tildes en búsquedas por defecto
        query_normalizado = normalizar(query)
        patients = [
            p for p in patients
            if query_normalizado in normalizar(p.first_name)
            or query_normalizado in normalizar(p.last_name)
            or query_normalizado in p.dni.lower()
            or query_normalizado in p.phone.lower()
        ]

    paginator = Paginator(patients, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'patients/list.html', {
        'patients': page_obj,
        'query': query,
        'page_obj': page_obj,
    })


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, 'patients/detail.html', {'patient': patient})


@login_required
def patient_create(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('patients:list')
    else:
        form = PatientForm()

    return render(request, 'patients/form.html', {
        'form': form,
        'title': 'Nuevo paciente',
    })


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('patients:detail', pk=patient.pk)
    else:
        form = PatientForm(instance=patient)

    return render(request, 'patients/form.html', {
        'form': form,
        'title': f'Editar — {patient.full_name}',
        'patient': patient,
    })