# backend/apps/bonuses/models.py
# Modelo de bono — representa un pack de sesiones comprado por un paciente.

from django.db import models
from apps.patients.models import Patient


class Bonus(models.Model):

    class BonusType(models.IntegerChoices):
        FIVE = 5, '5 sesiones'
        TEN = 10, '10 sesiones'

    # on_delete=PROTECT evita borrar un paciente que tiene bonos asociados
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='bonuses',  # acceso inverso: patient.bonuses.all()
        verbose_name='Paciente'
    )

    # blank=True porque el número se genera automáticamente en save(), no lo introduce el usuario
    bonus_number = models.CharField(
        max_length=10,
        unique=True,
        blank=True,
        verbose_name='Número de bono'
    )

    bonus_type = models.IntegerField(
        choices=BonusType.choices,
        verbose_name='Tipo de bono'
    )

    # Empieza en 0 y se incrementa con cada venta asociada al bono
    sessions_used = models.PositiveIntegerField(
        default=0,
        verbose_name='Sesiones consumidas'
    )

    # Se desactiva automáticamente cuando sessions_used alcanza bonus_type
    is_active = models.BooleanField(default=True, verbose_name='Activo')

    created_at = models.DateField(auto_now_add=True, verbose_name='Fecha de creación')

    class Meta:
        verbose_name = 'Bono'
        verbose_name_plural = 'Bonos'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.bonus_number} — {self.patient} ({self.get_bonus_type_display()})'

    @property
    def sessions_remaining(self):
        return self.bonus_type - self.sessions_used

    def save(self, *args, **kwargs):
        if not self.bonus_number:
            # Tomamos el último ID para generar el siguiente número sin repetir nunca
            # zfill(3) formatea con ceros: 1 → 001, 42 → 042
            last = Bonus.objects.order_by('-id').first()
            last_num = int(last.bonus_number[1:]) if last and last.bonus_number else 0
            self.bonus_number = f'B{str(last_num + 1).zfill(3)}'

        # Si se agotaron las sesiones, desactivamos el bono
        if self.sessions_used >= self.bonus_type:
            self.is_active = False

        super().save(*args, **kwargs)