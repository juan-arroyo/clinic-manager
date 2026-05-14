# backend/apps/sales/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.core.mail import EmailMessage
from django.contrib import messages
from django.utils import timezone
from .models import Sale, Invoice
from .forms import SaleForm, InvoiceForm
from apps.bonuses.models import Bonus
from apps.patients.models import Patient
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import unicodedata


def normalizar(texto):
    # NFD separa caracteres de sus tildes, ascii las elimina: "García" → "garcia"
    return unicodedata.normalize('NFD', texto).encode('ascii', 'ignore').decode('utf-8').lower()


@login_required
def sale_list(request):
    query = request.GET.get('q', '')
    sales = Sale.objects.select_related('patient', 'worker', 'bonus')

    if query:
        # Filtramos en Python porque PostgreSQL no normaliza tildes por defecto
        query_normalizado = normalizar(query)
        sales = [
            s for s in sales
            if query_normalizado in normalizar(s.patient.first_name)
            or query_normalizado in normalizar(s.patient.last_name)
            or (s.invoice_number and query_normalizado in s.invoice_number.lower())
            or query_normalizado in normalizar(s.description)
        ]

    paginator = Paginator(sales, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'sales/list.html', {
        'sales': page_obj,
        'query': query,
        'page_obj': page_obj,
    })


@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/detail.html', {'sale': sale})


@login_required
def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            # is_bonus se deduce del campo bonus — si hay bono seleccionado, es venta de bono
            if sale.bonus is not None:
                sale.is_bonus = True
            sale.save()
            return redirect('sales:list')
    else:
        form = SaleForm()

    return render(request, 'sales/form.html', {
        'form': form,
        'title': 'Nueva venta',
    })


@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)

    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            return redirect('sales:detail', pk=sale.pk)
    else:
        form = SaleForm(instance=sale)

    return render(request, 'sales/form.html', {
        'form': form,
        'title': f'Editar venta — {sale.date}',
        'sale': sale,           # necesario para el botón de cancelar en el template
        'current_patient': sale.patient,
    })


@login_required
def get_patient_bonuses(request):
    """
    Vista HTMX — devuelve el desplegable de bonos actualizado al cambiar de paciente.
    """
    # HTMX puede enviar el ID como 'patient' o 'patient_id' según el atributo hx-include
    patient_id = request.GET.get('patient', '') or request.GET.get('patient_id', '')

    bonuses = Bonus.objects.filter(
        patient_id=patient_id, is_active=True
    ) if patient_id else Bonus.objects.none()

    return render(request, 'sales/partials/bonus_select.html', {'bonuses': bonuses})


@login_required
def search_patients_sales(request):
    """
    Vista HTMX — búsqueda de pacientes en tiempo real para el formulario de ventas.
    """
    query = request.GET.get('q', '').strip()

    if len(query) >= 2:
        query_normalizado = normalizar(query)
        patients = [
            p for p in Patient.objects.filter(is_active=True).order_by('last_name', 'first_name')
            if query_normalizado in normalizar(p.first_name)
            or query_normalizado in normalizar(p.last_name)
        ][:10]
    else:
        patients = []

    return render(request, 'sales/partials/patient_results.html', {
        'patients': patients,
        'query': query,
    })


@login_required
def generate_invoice_pdf(request, pk):
    """Genera y devuelve el PDF de una factura como descarga."""
    sale = get_object_or_404(Sale, pk=pk)
    invoice = get_object_or_404(Invoice, sale=sale)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="factura-{invoice.number}.pdf"'

    doc = SimpleDocTemplate(
        response, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    clinic_blue = colors.HexColor('#2596be')
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('ClinicTitle', parent=styles['Heading1'], fontSize=20, textColor=clinic_blue, spaceAfter=0.3*cm)
    normal_style = ParagraphStyle('ClinicNormal', parent=styles['Normal'], fontSize=10, spaceAfter=0.2*cm)
    small_style = ParagraphStyle('ClinicSmall', parent=styles['Normal'], fontSize=8, textColor=colors.grey)

    elements = []

    elements.append(Paragraph('Gestión Clínica', title_style))
    elements.append(Paragraph('Fisioterapia Deportiva', small_style))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Table([['']],colWidths=[17*cm], style=TableStyle([('LINEBELOW', (0,0), (-1,-1), 1, clinic_blue)])))
    elements.append(Spacer(1, 0.5*cm))

    invoice_table = Table(
        [['FACTURA', ''], [f'Nº {invoice.number}', f'Fecha: {invoice.issued_at.strftime("%d/%m/%Y")}']],
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

    elements.append(Paragraph('Datos del cliente', ParagraphStyle('SectionTitle', parent=styles['Normal'], fontSize=10, textColor=clinic_blue, fontName='Helvetica-Bold', spaceAfter=0.2*cm)))
    elements.append(Table(
        [['Nombre:', sale.patient.full_name], ['DNI:', sale.patient.dni]],
        colWidths=[3*cm, 14*cm],
        style=TableStyle([('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 4)])
    ))
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph('Detalle', ParagraphStyle('SectionTitle2', parent=styles['Normal'], fontSize=10, textColor=clinic_blue, fontName='Helvetica-Bold', spaceAfter=0.2*cm)))
    # split('\n') respeta saltos de línea del body; line or ' ' evita párrafos vacíos en ReportLab
    for line in invoice.body.split('\n'):
        elements.append(Paragraph(line or ' ', normal_style))
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Table(
        [['', 'TOTAL:', f'{sale.amount}€']],
        colWidths=[8*cm, 5*cm, 4*cm],
        style=TableStyle([
            ('FONTNAME', (1,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('TEXTCOLOR', (1,0), (-1,-1), clinic_blue),
            ('LINEABOVE', (1,0), (-1,-1), 1, clinic_blue),
            ('TOPPADDING', (0,0), (-1,-1), 8),
        ])
    ))
    elements.append(Spacer(1, 2.5*cm))
    elements.append(Table([['']],colWidths=[17*cm], style=TableStyle([('LINEABOVE', (0,0), (-1,-1), 0.5, colors.grey)])))
    elements.append(Paragraph('Gestión Clínica Fisioterapia Deportiva — Alicante', small_style))

    doc.build(elements)
    return response


@login_required
def invoice_create(request, pk):
    """
    Crea una factura para una venta.
    Pre-rellena el formulario con los datos de la venta y el paciente.
    """
    sale = get_object_or_404(Sale, pk=pk)

    if hasattr(sale, 'invoice'):
        return redirect('sales:invoice_detail', pk=pk)

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.sale = sale
            invoice.number = Invoice.generate_number(form.cleaned_data['issued_at'].year)
            invoice.save()
            sale.invoice_issued = True
            sale.invoice_number = invoice.number
            sale.save()
            return redirect('sales:invoice_detail', pk=pk)
    else:
        body_default = (
            f"Paciente: {sale.patient.full_name}\n"
            f"DNI: {sale.patient.dni}\n\n"
            f"Concepto: {sale.get_treatment_type_display()}\n"
            f"Fecha de la sesión: {sale.date.strftime('%d/%m/%Y')}\n\n"
            f"Importe: {sale.amount}€\n"
            f"Método de pago: {sale.get_payment_method_display()}\n"
        )
        form = InvoiceForm(initial={
            'issued_at': timezone.localdate(),
            'recipient_email': sale.patient.email,
            'body': body_default,
        })

    return render(request, 'sales/invoice_form.html', {
        'form': form,
        'sale': sale,
        'title': 'Crear factura',
    })


@login_required
def invoice_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    invoice = get_object_or_404(Invoice, sale=sale)

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('sales:invoice_detail', pk=pk)
    else:
        form = InvoiceForm(instance=invoice)

    return render(request, 'sales/invoice_form.html', {
        'form': form,
        'sale': sale,
        'invoice': invoice,
        'title': f'Editar factura {invoice.number}',
    })


@login_required
def invoice_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    invoice = get_object_or_404(Invoice, sale=sale)
    return render(request, 'sales/invoice_detail.html', {'sale': sale, 'invoice': invoice})


@login_required
def invoice_send(request, pk):
    """
    Envía la factura por email con el PDF adjunto.
    Genera el PDF en memoria (BytesIO), lo adjunta y registra el envío en last_sent_at.
    Solo acepta POST — nunca GET, para evitar envíos accidentales desde un enlace.
    """
    sale = get_object_or_404(Sale, pk=pk)
    invoice = get_object_or_404(Invoice, sale=sale)

    # Solo POST — un enlace GET nunca debe disparar un envío de email
    if request.method != 'POST':
        return redirect('sales:invoice_detail', pk=pk)

    # PDF generado en BytesIO — en memoria, sin escribir en disco
    from io import BytesIO
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    clinic_blue = colors.HexColor('#2596be')
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=10, leading=14)
    small_style = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)

    elements = []
    header_table = Table([[
        Paragraph('<b><font color="#2596be" size="16">Gestión Clínica</font></b><br/><font color="grey" size="9">Fisioterapia Deportiva</font>', normal_style),
        Paragraph(f'<font color="grey" size="8">Nº Factura</font><br/><b>{invoice.number}</b><br/><font color="grey" size="8">Fecha de emisión</font><br/>{invoice.issued_at.strftime("%d/%m/%Y")}',
                  ParagraphStyle('right', parent=styles['Normal'], fontSize=10, alignment=2)),
    ]], colWidths=[10*cm, 7*cm])
    header_table.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'), ('LINEBELOW',(0,0),(-1,-1),1,clinic_blue), ('BOTTOMPADDING',(0,0),(-1,-1),12)]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph('<font color="grey" size="8">CLIENTE</font>', normal_style))
    elements.append(Paragraph(f'<b>{sale.patient.full_name}</b>', normal_style))
    elements.append(Paragraph(f'DNI: {sale.patient.dni}', normal_style))
    if sale.patient.email:
        elements.append(Paragraph(f'Email: {sale.patient.email}', normal_style))
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Paragraph('<font color="#2596be"><b>Detalle</b></font>',
        ParagraphStyle('section', parent=styles['Normal'], fontSize=10, textColor=clinic_blue, fontName='Helvetica-Bold', spaceAfter=0.2*cm)))
    for line in invoice.body.split('\n'):
        elements.append(Paragraph(line or ' ', normal_style))
    elements.append(Spacer(1, 0.5*cm))

    elements.append(Table([['', 'TOTAL:', f'{sale.amount}€']], colWidths=[8*cm, 5*cm, 4*cm],
        style=TableStyle([('FONTNAME',(1,0),(-1,-1),'Helvetica-Bold'), ('FONTSIZE',(0,0),(-1,-1),12),
                          ('ALIGN',(2,0),(2,-1),'RIGHT'), ('TEXTCOLOR',(1,0),(-1,-1),clinic_blue),
                          ('LINEABOVE',(1,0),(-1,-1),1,clinic_blue), ('TOPPADDING',(0,0),(-1,-1),8)])))
    elements.append(Spacer(1, 2*cm))
    elements.append(Table([['']],colWidths=[17*cm],style=TableStyle([('LINEABOVE',(0,0),(-1,-1),0.5,colors.grey)])))
    elements.append(Paragraph('Gestión Clínica Fisioterapia Deportiva — Alicante', small_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    email = EmailMessage(
        subject=f'Factura {invoice.number} — Clínica Fisioterapia',
        body=(
            f'Estimado/a {sale.patient.full_name},\n\n'
            f'Adjuntamos su factura {invoice.number} '
            f'correspondiente a la sesión del {sale.date.strftime("%d/%m/%Y")}.\n\n'
            f'Importe: {sale.amount}€\n\n'
            f'Un saludo,\nClínica Fisioterapia Deportiva'
        ),
        from_email=None,  # usa DEFAULT_FROM_EMAIL del settings
        to=[invoice.recipient_email],
    )
    # '/' no es válido en nombres de archivo — se reemplaza por '-'
    email.attach(f'factura_{invoice.number.replace("/", "-")}.pdf', pdf_bytes, 'application/pdf')
    email.send()

    invoice.last_sent_at = timezone.now()
    invoice.save()

    messages.success(request, f'Factura enviada correctamente a {invoice.recipient_email}.')
    return redirect('sales:invoice_detail', pk=pk)