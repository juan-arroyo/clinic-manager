# backend/apps/patients/forms.py
# Formulario de paciente.
# Django genera automáticamente los campos a partir del modelo.

from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):
    # ModelForm crea automáticamente los campos del formulario
    # basándose en los campos del modelo Patient

    class Meta:
        model = Patient      # modelo del que generamos el formulario
        fields = [           # campos que incluimos en el formulario
            'dni',
            'first_name',
            'last_name',
            'birth_date',
            'phone',
            'email',
            'address',
            'notes',
            'is_active',
        ]
        # Personalizamos los widgets (el tipo de input HTML de cada campo)
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '12345678A'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Apellidos'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'input input-bordered w-full',
                'type': 'date'  # input de tipo fecha nativo del navegador
            }),
            'phone': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': '600 000 000'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'paciente@email.com'
            }),
            'address': forms.TextInput(attrs={
                'class': 'input input-bordered w-full',
                'placeholder': 'Calle, número, ciudad'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'textarea textarea-bordered w-full',
                'rows': 3,
                'placeholder': 'Observaciones clínicas...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'checkbox'
            }),
        }