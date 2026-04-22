# backend/apps/patients/views.py
# Vistas del módulo de pacientes.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Q permite hacer búsquedas complejas (OR, AND)
from .models import Patient
from .forms import PatientForm  # lo crearemos en el siguiente paso


@login_required
def patient_list(request):
    # Recogemos el término de búsqueda de la URL (?q=texto)
    query = request.GET.get('q', '')  # si no hay búsqueda, q es cadena vacía

    # Empezamos con todos los pacientes activos
    patients = Patient.objects.filter(is_active=True)

    if query:
        # Q() permite buscar en varios campos a la vez con OR
        # icontains = contiene el texto, sin distinguir mayúsculas
        patients = patients.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(dni__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'patients/list.html', {
        'patients': patients,   # lista de pacientes para mostrar en la template
        'query': query,         # término de búsqueda para mantenerlo en el input
    })


@login_required
def patient_detail(request, pk):
    # get_object_or_404 busca el paciente por ID
    # Si no existe, devuelve automáticamente una página de error 404
    patient = get_object_or_404(Patient, pk=pk)
    return render(request, 'patients/detail.html', {'patient': patient})


@login_required
def patient_create(request):
    if request.method == 'POST':
        # Creamos el formulario con los datos enviados
        form = PatientForm(request.POST)
        if form.is_valid():
            # save() guarda el paciente en la base de datos y devuelve el objeto
            patient = form.save()
            # Redirigimos al detalle del paciente recién creado
            return redirect('patients:list')
    else:
        # GET: mostramos el formulario vacío
        form = PatientForm()

    return render(request, 'patients/form.html', {
        'form': form,
        'title': 'Nuevo paciente',  # título de la página
    })


@login_required
def patient_edit(request, pk):
    # Buscamos el paciente a editar
    patient = get_object_or_404(Patient, pk=pk)

    if request.method == 'POST':
        # instance=patient le dice al formulario que actualice este paciente
        # en lugar de crear uno nuevo
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            return redirect('patients:detail', pk=patient.pk)
    else:
        # GET: mostramos el formulario con los datos actuales del paciente
        form = PatientForm(instance=patient)

    return render(request, 'patients/form.html', {
        'form': form,
        'title': f'Editar — {patient.full_name}',
        'patient': patient,  # lo pasamos para poder mostrar botón de cancelar
    })