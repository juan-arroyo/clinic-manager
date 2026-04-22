# backend/apps/sales/views.py
# Vistas del módulo de ventas.
# Cada función maneja una URL y devuelve una respuesta HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Q permite búsquedas complejas con OR
from .models import Sale
from .forms import SaleForm


@login_required
def sale_list(request):
    # Recogemos el término de búsqueda de la URL (?q=texto)
    query = request.GET.get('q', '')

    # select_related trae los datos relacionados (paciente, trabajador, bono)
    # en una sola consulta SQL en lugar de una por cada fila — más eficiente
    sales = Sale.objects.select_related('patient', 'worker', 'bonus')

    if query:
        # Buscamos en varios campos a la vez usando OR
        sales = sales.filter(
            Q(patient__first_name__icontains=query) |   # nombre del paciente
            Q(patient__last_name__icontains=query) |    # apellidos del paciente
            Q(invoice_number__icontains=query) |        # número de factura
            Q(description__icontains=query)             # descripción
        )

    return render(request, 'sales/list.html', {
        'sales': sales,       # lista de ventas para mostrar en la template
        'query': query,       # término de búsqueda para mantenerlo en el input
    })


@login_required
def sale_detail(request, pk):
    # get_object_or_404 busca la venta por ID o devuelve error 404 si no existe
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/detail.html', {'sale': sale})


@login_required
def sale_create(request):
    if request.method == 'POST':
        # Creamos el formulario con los datos enviados
        form = SaleForm(request.POST)
        if form.is_valid():
            # save() ejecuta toda la lógica del modelo (factura, tarifa, bono)
            form.save()
            return redirect('sales:list')
    else:
        # GET: mostramos el formulario vacío
        form = SaleForm()

    return render(request, 'sales/form.html', {
        'form': form,
        'title': 'Nueva venta',
    })


@login_required
def sale_edit(request, pk):
    # Buscamos la venta a editar
    sale = get_object_or_404(Sale, pk=pk)

    if request.method == 'POST':
        # instance=sale le dice al formulario que actualice esta venta
        # en lugar de crear una nueva
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            return redirect('sales:detail', pk=sale.pk)
    else:
        # GET: mostramos el formulario con los datos actuales de la venta
        form = SaleForm(instance=sale)

    return render(request, 'sales/form.html', {
        'form': form,
        'title': f'Editar venta — {sale.date}',
        'sale': sale,  # lo pasamos para el botón de cancelar
    })