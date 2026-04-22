# backend/apps/sales/forms.py
# Formulario de venta.
# Este es el formulario más complejo del proyecto porque tiene lógica dinámica:
# el desplegable de bonos cambia según el paciente seleccionado.

from django import forms
from .models import Sale, FisioRate
from apps.patients.models import Patient
from apps.bonuses.models import Bonus
from django.contrib.auth import get_user_model

# get_user_model() devuelve el modelo de usuario personalizado (apps.users.User)
# Es la forma correcta de referenciarlo sin importarlo directamente
User = get_user_model()


class SaleForm(forms.ModelForm):

    class Meta:
        model = Sale
        fields = [
            'invoice_issued',
            'date',
            'patient',
            'amount',
            'is_bonus',
            'bonus',
            'payment_method',
            'worker',
            'treatment_type',
            'description',
            'is_paid',
        ]
        widgets = {
            # Input de fecha nativo del navegador
            'date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date'
            }),
            # Desplegable de pacientes
            'patient': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            # Campo de importe
            'amount': forms.NumberInput(attrs={
                'class': 'input input-bordered w-full',
                'step': '0.01',      # permite decimales de 2 cifras
                'placeholder': '0.00'
            }),
            # Desplegable de bonos — se filtrará dinámicamente con HTMX más adelante
            'bonus': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            # Desplegable de método de pago
            'payment_method': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            # Desplegable de trabajador
            'worker': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            # Desplegable de tipo de tratamiento
            'treatment_type': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            # Área de texto para la descripción
            'description': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 2,
                'placeholder': 'Descripción opcional...'
            }),
            # Checkboxes
            'invoice_issued': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'is_bonus': forms.CheckboxInput(attrs={'class': 'checkbox'}),
            'is_paid': forms.CheckboxInput(attrs={'class': 'checkbox'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Solo mostramos pacientes activos en el desplegable
        self.fields['patient'].queryset = Patient.objects.filter(
            is_active=True
        ).order_by('last_name', 'first_name')
        self.fields['patient'].label = 'Paciente'

        # Solo mostramos bonos activos en el desplegable
        # El usuario deberá seleccionar primero el paciente y luego el bono
        self.fields['bonus'].queryset = Bonus.objects.filter(
            is_active=True
        ).select_related('patient').order_by('patient__last_name')
        self.fields['bonus'].label = 'Bono'
        self.fields['bonus'].required = False  # el bono es opcional

        # Solo mostramos fisioterapeutas activos como trabajadores
        self.fields['worker'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name')
        self.fields['worker'].label = 'Trabajador'

        # Etiquetas en español para el resto de campos
        self.fields['invoice_issued'].label = 'Factura emitida'
        self.fields['date'].label = 'Fecha'
        self.fields['amount'].label = 'Importe (€)'
        self.fields['is_bonus'].label = 'Es de bono'
        self.fields['payment_method'].label = 'Método de pago'
        self.fields['treatment_type'].label = 'Tipo de tratamiento'
        self.fields['description'].label = 'Descripción'
        self.fields['is_paid'].label = 'Pagado'