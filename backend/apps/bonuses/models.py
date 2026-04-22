# backend/apps/bonuses/models.py
# Modelo de bono — representa un pack de sesiones comprado por un paciente.

from django.db import models
from apps.patients.models import Patient  # relación con el paciente


class Bonus(models.Model):

    # Tipos de bono disponibles
    class BonusType(models.IntegerChoices):
        # IntegerChoices guarda un número pero muestra un texto legible
        FIVE = 5, '5 sesiones'
        TEN = 10, '10 sesiones'

    # --- RELACIÓN ---
    # ForeignKey crea una relación muchos-a-uno: un paciente puede tener varios bonos
    # on_delete=PROTECT evita borrar un paciente si tiene bonos asociados
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='bonuses',  # permite acceder a los bonos desde el paciente: patient.bonuses.all()
        verbose_name='Paciente'
    )

    # --- CAMPOS ---
    # Número de bono generado automáticamente: B01, B02, B03...
    # blank=True porque lo generamos en el método save(), no el usuario
    bonus_number = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        verbose_name='Número de bono'
    )

    # Tipo de bono: 5 o 10 sesiones
    bonus_type = models.IntegerField(
        choices=BonusType.choices,
        verbose_name='Tipo de bono'
    )

    # Sesiones ya consumidas — empieza en 0 y sube con cada venta
    sessions_used = models.PositiveIntegerField(
        default=0,
        verbose_name='Sesiones consumidas'
    )

    # El bono se desactiva automáticamente al agotar sesiones
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    # Fecha de creación del bono
    created_at = models.DateField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        verbose_name = 'Bono'
        verbose_name_plural = 'Bonos'
        ordering = ['-created_at']  # los más recientes primero

    def __str__(self):
        return f'{self.bonus_number} — {self.patient} ({self.get_bonus_type_display()})'

    @property
    def sessions_remaining(self):
        # Sesiones que quedan en el bono
        return self.bonus_type - self.sessions_used

    def save(self, *args, **kwargs):
        # Si el bono es nuevo (no tiene número asignado todavía), lo generamos
        if not self.bonus_number:
            # Contamos cuántos bonos existen para generar el siguiente número
            # zfill(3) rellena con ceros a la izquierda: 1 → 001
            last = Bonus.objects.count()
            self.bonus_number = f'B{str(last + 1).zfill(3)}'

        # Si se han consumido todas las sesiones, desactivamos el bono
        if self.sessions_used >= self.bonus_type:
            self.is_active = False

        super().save(*args, **kwargs)