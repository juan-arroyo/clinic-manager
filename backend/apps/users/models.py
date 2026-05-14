# backend/apps/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Email como identificador principal en lugar de username.
    # Debe definirse antes de la primera migración — no se puede cambiar después.
    email = models.EmailField(unique=True)

    class Role(models.TextChoices):
        OWNER = 'owner', 'Propietario'
        PHYSIO = 'physio', 'Fisioterapeuta'

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PHYSIO,
    )

    # Color en formato hexadecimal, ej: #FF5733
    color = models.CharField(max_length=7, default='#3B82F6')

    # Django usa este campo para autenticar en lugar de username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER


class Physio(models.Model):
    """
    Fisioterapeutas/trabajadores de la clínica.
    No tienen acceso al sistema — solo aparecen en ventas y reportes.
    """
    first_name = models.CharField(max_length=100, verbose_name='Nombre')
    last_name = models.CharField(max_length=100, verbose_name='Apellidos')
    color = models.CharField(
        max_length=7,
        default='#3B82F6',
        verbose_name='Color identificativo'
    )
    # is_active permite desactivar fisios que ya no trabajan sin borrar su historial
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    class Meta:
        verbose_name = 'Fisioterapeuta'
        verbose_name_plural = 'Fisioterapeutas'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'