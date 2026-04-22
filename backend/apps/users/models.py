# backend/apps/users/models.py
# Modelo de usuario personalizado.
# Lo creamos extendiendo AbstractUser de Django, que ya incluye
# campos como username, email, password, first_name, last_name, etc.
# Añadimos los campos específicos de nuestra clínica.

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Usamos email como identificador principal en lugar de username
    # (lección aprendida: definir esto ANTES de la primera migración)
    email = models.EmailField(unique=True)  # el email debe ser único por usuario

    # Roles disponibles en la clínica
    class Role(models.TextChoices):
        # TextChoices crea un conjunto de opciones con valor y etiqueta
        OWNER = 'owner', 'Propietario'
        PHYSIO = 'physio', 'Fisioterapeuta'

    # Campo de rol — por defecto es fisioterapeuta
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PHYSIO,
    )

    # Color identificativo del fisioterapeuta (se mostrará en la interfaz)
    # Guardamos el color en formato hexadecimal, ej: #FF5733
    color = models.CharField(max_length=7, default='#3B82F6')

    # Le decimos a Django que use el email para hacer login
    # en lugar del username
    USERNAME_FIELD = 'email'

    # Campos requeridos al crear un usuario por terminal (además del email y password)
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        # Representación legible del usuario (aparece en el admin)
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def is_owner(self):
        # Propiedad de conveniencia para comprobar si el usuario es propietario
        return self.role == self.Role.OWNER