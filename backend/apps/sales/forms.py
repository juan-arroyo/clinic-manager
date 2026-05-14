# backend/apps/sales/forms.py

from django import forms
from .models import Sale, FisioRate, Invoice
from apps.patients.models import Patient
from apps.bonuses.models import Bonus
from apps.users.models import Physio


class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale
        fields = [
            'date', 'patient', 'amount', 'is_bonus', 'bonus',
            'payment_method', 'worker', 'treatment_type', 'description',
        ]
        widgets = {
            'date': forms.DateInput(
                format='%Y-%m-%d',  # formato requerido por input type="date"
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'date'
                }
            ),
            'patient': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'amount': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'bonus': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'payment_method': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'worker': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'treatment_type': forms.Select(attrs={'class': 'select select-bordered w-full'}),
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Descripción opcional...'
            }),
            'is_bonus': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['patient'].queryset = Patient.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['patient'].label = 'Paciente'

        self.fields['bonus'].queryset = Bonus.objects.filter(
            is_active=True
        ).select_related('patient').order_by('patient__last_name')
        self.fields['bonus'].label = 'Bono'
        self.fields['bonus'].required = False  # el bono es opcional — solo aplica a ventas de bono

        self.fields['worker'].queryset = Physio.objects.filter(
            is_active=True
        ).order_by('first_name')
        self.fields['worker'].label = 'Trabajador'

        self.fields['date'].label = 'Fecha'
        self.fields['amount'].label = 'Importe (€)'
        self.fields['is_bonus'].label = 'Es de bono'
        self.fields['payment_method'].label = 'Método de pago'
        self.fields['treatment_type'].label = 'Tipo de tratamiento'
        self.fields['description'].label = 'Descripción'


class InvoiceForm(forms.ModelForm):
    """
    Formulario para crear y editar facturas.
    Se pre-rellena con los datos de la venta pero todo es editable antes de emitir.
    """

    class Meta:
        model = Invoice
        fields = ['issued_at', 'recipient_email', 'body']
        widgets = {
            'issued_at': forms.DateInput(
                format='%Y-%m-%d',  # formato requerido por input type="date"
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'date'
                }
            ),
            'recipient_email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
            }),
            'body': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 10,
                'placeholder': 'Descripción de los servicios prestados...'
            }),
        }
        labels = {
            'issued_at': 'Fecha de emisión',
            'recipient_email': 'Email destinatario',
            'body': 'Cuerpo de la factura',
        }