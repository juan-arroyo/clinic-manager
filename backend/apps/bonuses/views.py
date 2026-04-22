# backend/apps/bonuses/views.py
# Vistas del módulo de bonos.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Bonus
from .forms import BonusForm


@login_required
def bonus_list(request):
    query = request.GET.get('q', '')

    # Por defecto mostramos todos los bonos
    bonuses = Bonus.objects.select_related('patient')  # select_related optimiza la consulta
                                                        # trayendo el paciente en la misma query

    if query:
        bonuses = bonuses.filter(
            Q(bonus_number__icontains=query) |
            Q(patient__first_name__icontains=query) |
            Q(patient__last_name__icontains=query)
        )

    return render(request, 'bonuses/list.html', {
        'bonuses': bonuses,
        'query': query,
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