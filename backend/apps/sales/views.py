# backend/apps/sales/views.py
# Vistas del módulo de ventas.
# Cada función maneja una URL y devuelve una respuesta HTTP.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q  # Q permite búsquedas complejas con OR
from .models import Sale
from .forms import SaleForm
from apps.bonuses.models import Bonus
from reportlab.lib.pagesizes import A4          # tamaño de página A4
from reportlab.lib.units import cm              # unidades en centímetros
from reportlab.lib import colors                # colores para el PDF
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from django.http import HttpResponse


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


@login_required
def get_patient_bonuses(request):
    """
    Vista llamada por HTMX cuando el usuario selecciona un paciente.
    Devuelve solo el HTML del desplegable de bonos actualizado.
    """
    # HTMX envía el valor del select con el nombre del campo
    # puede venir como 'patient' o 'patient_id' dependiendo del atributo hx-include
    patient_id = request.GET.get('patient', '') or request.GET.get('patient_id', '')

    if patient_id:
        # Filtramos los bonos activos del paciente seleccionado
        bonuses = Bonus.objects.filter(
            patient_id=patient_id,
            is_active=True
        )
    else:
        # Si no hay paciente, no mostramos bonos
        bonuses = Bonus.objects.none()

    # Renderizamos solo el fragmento del desplegable
    return render(request, 'sales/partials/bonus_select.html', {
        'bonuses': bonuses
    })



@login_required
def generate_invoice_pdf(request, pk):
    """
    Genera el PDF de una factura y lo devuelve para descarga.
    Solo se puede generar si la venta tiene factura emitida.
    """
    # Buscamos la venta
    sale = get_object_or_404(Sale, pk=pk)

    # Solo generamos PDF si la factura está emitida
    if not sale.invoice_issued:
        from django.contrib import messages
        messages.error(request, 'Esta venta no tiene factura emitida.')
        return redirect('sales:detail', pk=pk)

    # Preparamos la respuesta HTTP para descarga de PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura-{sale.invoice_number}.pdf"'

    # Creamos el documento PDF en memoria
    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    # Color principal de la clínica
    clinic_blue = colors.HexColor('#2596be')

    # Estilos de texto
    styles = getSampleStyleSheet()

    # Estilo para el título principal
    title_style = ParagraphStyle(
        'ClinicTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=clinic_blue,
        spaceAfter=0.3*cm,
    )

    # Estilo para texto normal
    normal_style = ParagraphStyle(
        'ClinicNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=0.2*cm,
    )

    # Estilo para texto pequeño
    small_style = ParagraphStyle(
        'ClinicSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
    )

    # Lista de elementos que formarán el PDF (de arriba a abajo)
    elements = []

    # --- CABECERA --- #

    # Nombre de la clínica
    elements.append(Paragraph('Clínica Solaz', title_style))
    elements.append(Paragraph('Fisioterapia Deportiva', small_style))
    elements.append(Spacer(1, 0.5*cm))  # espacio en blanco

    # Línea separadora
    elements.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([
            ('LINEBELOW', (0,0), (-1,-1), 1, clinic_blue),
        ])
    ))
    elements.append(Spacer(1, 0.5*cm))

    # --- DATOS DE LA FACTURA --- #

    # Tabla con número de factura y fecha
    invoice_data = [
        ['FACTURA', ''],
        [f'Nº {sale.invoice_number}', f'Fecha: {sale.date.strftime("%d/%m/%Y")}'],
    ]

    invoice_table = Table(
        invoice_data,
        colWidths=[8.5*cm, 8.5*cm],
        style=TableStyle([
            ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (0,0), 14),
            ('TEXTCOLOR', (0,0), (0,0), clinic_blue),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTSIZE', (0,1), (-1,-1), 10),
        ])
    )
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.5*cm))

    # --- DATOS DEL PACIENTE --- #
    elements.append(Paragraph('Datos del cliente', ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=clinic_blue,
        fontName='Helvetica-Bold',
        spaceAfter=0.2*cm,
    )))

    client_data = [
        ['Nombre:', sale.patient.full_name],
        ['DNI:', sale.patient.dni],
    ]

    client_table = Table(
        client_data,
        colWidths=[3*cm, 14*cm],
        style=TableStyle([
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ])
    )
    elements.append(client_table)
    elements.append(Spacer(1, 0.5*cm))

    # --- DETALLE DE LA VENTA --- #
    elements.append(Paragraph('Detalle', ParagraphStyle(
        'SectionTitle2',
        parent=styles['Normal'],
        fontSize=10,
        textColor=clinic_blue,
        fontName='Helvetica-Bold',
        spaceAfter=0.2*cm,
    )))

    # Cabecera de la tabla de detalle
    detail_data = [
        ['Descripción', 'Tipo de tratamiento', 'Importe'],
        [
            sale.description or 'Sesión de fisioterapia',
            sale.get_treatment_type_display(),
            f'{sale.amount}€',
        ]
    ]

    detail_table = Table(
        detail_data,
        colWidths=[8*cm, 5*cm, 4*cm],
        style=TableStyle([
            # Cabecera con fondo azul
            ('BACKGROUND', (0,0), (-1,0), clinic_blue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),  # importe alineado a la derecha
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f6fa')]),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d2e6f2')),
        ])
    )
    elements.append(detail_table)
    elements.append(Spacer(1, 0.5*cm))

    # --- TOTAL --- #
    total_data = [
        ['', 'TOTAL:', f'{sale.amount}€'],
    ]

    total_table = Table(
        total_data,
        colWidths=[8*cm, 5*cm, 4*cm],
        style=TableStyle([
            ('FONTNAME', (1,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('TEXTCOLOR', (1,0), (-1,-1), clinic_blue),
            ('LINEABOVE', (1,0), (-1,-1), 1, clinic_blue),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ])
    )
    elements.append(total_table)
    elements.append(Spacer(1, 0.5*cm))

    # --- MÉTODO DE PAGO --- #
    elements.append(Paragraph(
        f'Método de pago: {sale.get_payment_method_display()}',
        normal_style
    ))

    # --- PIE DE PÁGINA --- #
    elements.append(Spacer(1, 2*cm))
    elements.append(Table(
        [['']],
        colWidths=[17*cm],
        style=TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 0.5, colors.grey),
        ])
    ))
    elements.append(Paragraph(
        'Clínica Solaz Fisioterapia Deportiva — Alicante',
        small_style
    ))

    # Construimos el PDF con todos los elementos
    doc.build(elements)

    return response