# backend/apps/bonuses/forms.py
# Formulario de bono.

from django import forms
from .models import Bonus
from apps.patients.models import Patient


class BonusForm(forms.ModelForm):

    class Meta:
        model = Bonus
        fields = ['patient', 'bonus_type']  # solo estos dos — el resto se genera automáticamente
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
            'bonus_type': forms.Select(attrs={
                'class': 'select select-bordered w-full',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostramos solo pacientes activos en el desplegable
        self.fields['patient'].queryset = Patient.objects.filter(is_active=True).order_by('last_name', 'first_name')
        # Etiqueta legible para el campo
        self.fields['patient'].label = 'Paciente'
        self.fields['bonus_type'].label = 'Tipo de bono'