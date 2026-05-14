# backend/apps/sales/models.py

from django.db import models
from django.utils import timezone
from apps.patients.models import Patient
from apps.bonuses.models import Bonus
from apps.users.models import Physio


class FisioRate(models.Model):
    """
    Tabla de tarifas por fisioterapeuta y tipo de tratamiento.
    Se configura desde el admin y se consulta automáticamente al registrar cada venta.
    """

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

    fisio = models.ForeignKey(
        Physio,
        on_delete=models.CASCADE,
        related_name='rates',
        verbose_name='Fisioterapeuta'
    )
    treatment_type = models.CharField(
        max_length=20,
        choices=TreatmentType.choices,
        verbose_name='Tipo de tratamiento'
    )
    # Diferencia la tarifa normal de la tarifa cuando la sesión es de bono
    is_bonus = models.BooleanField(default=False, verbose_name='Es de bono')
    rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Tarifa (€)'
    )

    class Meta:
        verbose_name = 'Tarifa de fisioterapeuta'
        verbose_name_plural = 'Tarifas de fisioterapeutas'
        # Combinación única: un fisio no puede tener dos tarifas para el mismo tipo y modalidad
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

    invoice_issued = models.BooleanField(default=False, verbose_name='Factura emitida')
    # null=True es necesario para que múltiples ventas sin factura no colisionen en el unique
    invoice_number = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        null=True,
        verbose_name='Número de factura'
    )
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
        on_delete=models.SET_NULL,  # si se borra el bono, la venta se conserva sin referencia
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
        Physio,
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

    # Calculado automáticamente en save() consultando FisioRate
    fisio_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Importe fisioterapeuta (€)'
    )

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
        count = Sale.objects.filter(
            invoice_issued=True,
            date__year=year,
            invoice_number__isnull=False
        ).count()
        return f'{year}/{str(count + 1).zfill(3)}'

    def calculate_fisio_amount(self):
        """Calcula el importe del fisioterapeuta según la tabla FisioRate."""
        try:
            rate = FisioRate.objects.get(
                fisio=self.worker,
                treatment_type=self.treatment_type,
                is_bonus=self.is_bonus
            )
            return rate.rate
        except FisioRate.DoesNotExist:
            return 0  # si no hay tarifa configurada para esta combinación, no se imputa nada

    def save(self, *args, **kwargs):
        if self.invoice_issued and not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        self.fisio_amount = self.calculate_fisio_amount()

        # pk is None indica que es una venta nueva, no una edición
        # Solo incrementamos el bono en creación — no en cada guardado
        is_new = self.pk is None
        if is_new and self.is_bonus and self.bonus:
            self.bonus.sessions_used += 1
            self.bonus.save()  # el save() del bono verifica si debe desactivarse

        super().save(*args, **kwargs)


class Invoice(models.Model):
    """
    Factura asociada a una venta.
    Se crea por separado — una venta puede existir sin factura,
    y la factura se emite cuando el cliente la solicita.
    """

    # on_delete=PROTECT — no se puede eliminar una venta que tiene factura emitida
    sale = models.OneToOneField(
        Sale,
        on_delete=models.PROTECT,
        related_name='invoice',  # acceso desde la venta: sale.invoice
        verbose_name='Venta'
    )
    # Formato 2026/001 — generado automáticamente en la vista invoice_create
    number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Número de factura'
    )
    # Pre-rellenado con el email del paciente, pero editable antes de emitir
    recipient_email = models.EmailField(verbose_name='Email destinatario')

    # Texto libre pre-rellenado con los datos de la venta, editable antes de emitir
    body = models.TextField(verbose_name='Cuerpo de la factura')

    issued_at = models.DateField(verbose_name='Fecha de emisión')

    # null mientras no se haya enviado por email
    last_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Último envío por email'
    )

    class Meta:
        verbose_name = 'Factura'
        verbose_name_plural = 'Facturas'
        ordering = ['-issued_at']

    def __str__(self):
        return f'Factura {self.number} — {self.sale.patient.full_name}'

    @staticmethod
    def generate_number(year):
        """Genera el siguiente número de factura para el año indicado. Formato: 2026/001."""
        count = Invoice.objects.filter(issued_at__year=year).count()
        return f'{year}/{str(count + 1).zfill(3)}'