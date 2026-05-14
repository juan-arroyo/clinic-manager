# backend/apps/patients/models.py

from django.db import models


class Patient(models.Model):
    dni = models.CharField(
        max_length=20,
        unique=True,        # un DNI no puede pertenecer a dos pacientes
        verbose_name='DNI'
    )
    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellidos')
    birth_date = models.DateField(
        null=True, blank=True,  # opcional
        verbose_name='Fecha de nacimiento'
    )
    phone = models.CharField(max_length=20, blank=True, verbose_name='Teléfono')
    email = models.EmailField(blank=True, verbose_name='Correo electrónico')
    address = models.CharField(max_length=255, blank=True, verbose_name='Domicilio')
    registration_date = models.DateField(
        auto_now_add=True,  # se asigna automáticamente al crear el registro
        verbose_name='Fecha de alta'
    )
    notes = models.TextField(blank=True, verbose_name='Observaciones')
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.last_name}, {self.first_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'