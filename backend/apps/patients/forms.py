# backend/apps/patients/forms.py

from django import forms
from .models import Patient


class PatientForm(forms.ModelForm):

    class Meta:
        model = Patient
        fields = [
            'dni', 'first_name', 'last_name', 'birth_date',
            'phone', 'email', 'address', 'notes',
        ]
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
            'birth_date': forms.DateInput(
                format='%Y-%m-%d',  # formato requerido por input type="date"
                attrs={
                    'class': 'input input-bordered w-full',
                    'type': 'date'
                }
            ),
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