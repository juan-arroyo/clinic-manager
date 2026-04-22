# backend/apps/sales/models.py
# Modelos del módulo de ventas.

from django.db import models
from django.utils import timezone
from apps.patients.models import Patient
from apps.bonuses.models import Bonus
from django.conf import settings  # para referenciar el modelo de usuario


class FisioRate(models.Model):
    """
    Tabla de tarifas por fisioterapeuta y tipo de tratamiento.
    El propietario la configura desde el admin.
    El sistema la consulta al registrar cada venta.
    """

    # Tipos de tratamiento disponibles — misma lista que en Sale
    class TreatmentType(models.TextChoices):
        AVANZADA = 'avanzada', 'Avanzada'
        GENERAL = 'general', 'General'
        ONDAS = 'ondas', 'Ondas de choque'
        DINAMO = 'dinamo', 'Dinamo'
        EMG = 'emg', 'EMG'
        PROPIO = 'propio', 'Paciente propio'
        SABADO = 'sabado', 'Sábado'
        INFORME = 'informe', 'Informe'
        DOMICILIO = 'domicilio', 'A domicilio'
        BONO = 'bono', 'De bono'

    # Fisioterapeuta al que aplica esta tarifa
    fisio = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # referencia al modelo de usuario personalizado
        on_delete=models.CASCADE,
        related_name='rates',
        verbose_name='Fisioterapeuta'
    )

    # Tipo de tratamiento
    treatment_type = models.CharField(
        max_length=20,
        choices=TreatmentType.choices,
        verbose_name='Tipo de tratamiento'
    )

    # Si esta tarifa aplica a ventas de bono o no
    is_bonus = models.BooleanField(default=False, verbose_name='Es de bono')

    # La tarifa en euros
    rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Tarifa (€)'
    )

    class Meta:
        verbose_name = 'Tarifa de fisioterapeuta'
        verbose_name_plural = 'Tarifas de fisioterapeutas'
        # No puede haber dos tarifas iguales para el mismo fisio, tipo y bono
        unique_together = ['fisio', 'treatment_type', 'is_bonus']

    def __str__(self):
        bonus_str = ' (bono)' if self.is_bonus else ''
        return f'{self.fisio} — {self.get_treatment_type_display()}{bonus_str}: {self.rate}€'


class Sale(models.Model):
    """
    Registro de una venta o sesión en la clínica.
    """

    class PaymentMethod(models.TextChoices):
        CASH = 'efectivo', 'Efectivo'
        CARD = 'tarjeta', 'Tarjeta'
        BIZUM = 'bizum', 'Bizum'
        TRANSFER = 'transferencia', 'Transferencia'

    class TreatmentType(models.TextChoices):
        AVANZADA = 'avanzada', 'Avanzada'
        GENERAL = 'general', 'General'
        ONDAS = 'ondas', 'Ondas de choque'
        DINAMO = 'dinamo', 'Dinamo'
        EMG = 'emg', 'EMG'
        PROPIO = 'propio', 'Paciente propio'
        SABADO = 'sabado', 'Sábado'
        INFORME = 'informe', 'Informe'
        DOMICILIO = 'domicilio', 'A domicilio'
        BONO = 'bono', 'De bono'

    # --- FACTURACIÓN ---
    invoice_issued = models.BooleanField(default=False, verbose_name='Factura emitida')
    # Número de factura — formato 2026/001, generado automáticamente
    invoice_number = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        null=True,          # null=True permite que varios registros sin factura no colisionen en unique
        verbose_name='Número de factura'
    )

    # --- DATOS DE LA VENTA ---
    date = models.DateField(default=timezone.localdate, verbose_name='Fecha')
    patient = models.ForeignKey(
        Patient,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Paciente'
    )
    amount = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Importe (€)')
    is_bonus = models.BooleanField(default=False, verbose_name='Es de bono')
    bonus = models.ForeignKey(
        Bonus,
        on_delete=models.SET_NULL,  # si se borra el bono, la venta queda sin bono pero no se borra
        null=True,
        blank=True,
        related_name='sales',
        verbose_name='Bono'
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        verbose_name='Método de pago'
    )
    worker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='sales',
        verbose_name='Trabajador'
    )
    treatment_type = models.CharField(
        max_length=20,
        choices=TreatmentType.choices,
        verbose_name='Tipo de tratamiento'
    )
    description = models.TextField(blank=True, verbose_name='Descripción')
    is_paid = models.BooleanField(default=True, verbose_name='Pagado')

    # --- CÁLCULO AUTOMÁTICO ---
    # Lo que le corresponde al fisioterapeuta — se calcula automáticamente en save()
    fisio_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Importe fisioterapeuta (€)'
    )

    # --- METADATOS ---
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.date} — {self.patient} — {self.amount}€'

    def generate_invoice_number(self):
        """Genera el número de factura en formato AÑO/NNN."""
        year = self.date.year
        # Contamos las facturas emitidas este año
        count = Sale.objects.filter(
            invoice_issued=True,
            date__year=year,
            invoice_number__isnull=False
        ).count()
        return f'{year}/{str(count + 1).zfill(3)}'

    def calculate_fisio_amount(self):
        """Calcula lo que le corresponde al fisioterapeuta según la tabla de tarifas."""
        try:
            rate = FisioRate.objects.get(
                fisio=self.worker,
                treatment_type=self.treatment_type,
                is_bonus=self.is_bonus
            )
            return rate.rate
        except FisioRate.DoesNotExist:
            # Si no hay tarifa configurada, devolvemos 0
            return 0

    def save(self, *args, **kwargs):
        # Generamos el número de factura si se acaba de marcar como emitida
        if self.invoice_issued and not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        # Calculamos el importe del fisioterapeuta
        self.fisio_amount = self.calculate_fisio_amount()

        # Si es una venta de bono, incrementamos el contador del bono
        is_new = self.pk is None  # True si es una venta nueva (no una edición)
        if is_new and self.is_bonus and self.bonus:
            self.bonus.sessions_used += 1
            self.bonus.save()  # save() del bono comprueba si debe desactivarse

        super().save(*args, **kwargs)