# backend/apps/patients/models.py
# Modelo de paciente — representa la ficha de cada paciente de la clínica.

from django.db import models


class Patient(models.Model):
    # --- DATOS PERSONALES ---
    dni = models.CharField(
        max_length=20,
        unique=True,         # no puede haber dos pacientes con el mismo DNI
        verbose_name='DNI'
    )
    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellidos')
    birth_date = models.DateField(
        null=True, blank=True,  # campo opcional
        verbose_name='Fecha de nacimiento'
    )

    # --- CONTACTO ---
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Correo electrónico')
    address = models.CharField(max_length=255, blank=True, verbose_name='Domicilio')

    # --- DATOS CLÍNICOS ---
    registration_date = models.DateField(
        auto_now_add=True,   # se rellena automáticamente al crear el paciente
        verbose_name='Fecha de alta'
    )
    notes = models.TextField(blank=True, verbose_name='Observaciones')

    # --- METADATOS ---
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        # Nombre legible en el admin
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        # Ordenados por apellidos por defecto
        ordering = ['last_name', 'first_name']

    def __str__(self):
        # Representación legible: "García López, Juan"
        return f'{self.last_name}, {self.first_name}'

    @property
    def full_name(self):
        # Nombre completo en orden natural: "Juan García López"
        return f'{self.first_name} {self.last_name}'