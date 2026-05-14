# backend/apps/patients/management/commands/seed_data.py
#
# Comando personalizado de Django para generar datos de prueba.
# Se ejecuta con: python manage.py seed_data
#
# Genera:
#   - 100 pacientes con datos ficticios en español
#   - 40 bonos (asignados a pacientes aleatorios)
#   - 300 ventas (distribuidas en los últimos 6 meses)
#
# IMPORTANTE: Solo usar en desarrollo. Nunca en producción.

import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.patients.models import Patient
from apps.bonuses.models import Bonus
from apps.sales.models import Sale, FisioRate, Invoice
from apps.users.models import Physio


# ── DATOS FICTICIOS EN ESPAÑOL ──────────────────────────────────────────────

NOMBRES = [
    'María', 'Carmen', 'Ana', 'Isabel', 'Laura',
    'José', 'Antonio', 'Manuel', 'Francisco', 'David',
    'Lucía', 'Marta', 'Sara', 'Elena', 'Paula',
    'Carlos', 'Miguel', 'Javier', 'Alejandro', 'Sergio',
    'Rosa', 'Pilar', 'Cristina', 'Nuria', 'Mónica',
    'Pedro', 'Luis', 'Ángel', 'Rafael', 'Jorge',
]

APELLIDOS = [
    'García', 'Martínez', 'López', 'Sánchez', 'González',
    'Fernández', 'Pérez', 'Gómez', 'Martín', 'Jiménez',
    'Ruiz', 'Hernández', 'Díaz', 'Moreno', 'Muñoz',
    'Álvarez', 'Romero', 'Alonso', 'Gutiérrez', 'Navarro',
    'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil',
    'Ramírez', 'Serrano', 'Blanco', 'Suárez', 'Molina',
]

PREFIJOS_MOVIL = ['6', '7']
LETRAS_DNI = 'TRWAGMYFPDXBNJZSQVHLCKE'


# ── FUNCIONES AUXILIARES ─────────────────────────────────────────────────────

def generar_dni():
    """Genera un DNI español ficticio pero con formato válido."""
    numero = random.randint(10000000, 99999999)
    letra = LETRAS_DNI[numero % 23]
    return f'{numero}{letra}'


def generar_telefono():
    """Genera un número de móvil español ficticio."""
    prefijo = random.choice(PREFIJOS_MOVIL)
    resto = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f'{prefijo}{resto}'


def generar_fecha_nacimiento():
    """Genera una fecha de nacimiento aleatoria entre 20 y 75 años atrás."""
    hoy = date.today()
    años_atras = random.randint(20, 75)
    return hoy - timedelta(days=años_atras * 365 + random.randint(0, 364))


def generar_fecha_reciente(meses_atras=6):
    """Genera una fecha aleatoria dentro de los últimos N meses."""
    hoy = date.today()
    dias_atras = random.randint(1, meses_atras * 30)
    return hoy - timedelta(days=dias_atras)


def limpiar_texto(texto):
    """
    Elimina tildes y caracteres especiales para generar emails válidos.
    Ejemplo: 'María' → 'maria'
    """
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'a', 'É': 'e', 'Í': 'i', 'Ó': 'o', 'Ú': 'u',
        'ñ': 'n', 'Ñ': 'n', 'ü': 'u', 'Ü': 'u',
    }
    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)
    return texto.lower()


# ── COMANDO PRINCIPAL ────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = 'Genera datos de prueba: pacientes, bonos y ventas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pacientes', type=int, default=100,
            help='Número de pacientes a crear (por defecto: 100)'
        )
        parser.add_argument(
            '--bonos', type=int, default=40,
            help='Número de bonos a crear (por defecto: 40)'
        )
        parser.add_argument(
            '--ventas', type=int, default=300,
            help='Número de ventas a crear (por defecto: 300)'
        )
        parser.add_argument(
            '--limpiar', action='store_true',
            help='Borra todos los datos existentes antes de crear los nuevos'
        )

    def handle(self, *args, **options):

        # ── PASO 0: limpiar datos existentes si se pidió ──────────────────
        if options['limpiar']:
            self.stdout.write('🗑️  Borrando datos existentes...')
            # El orden importa: primero lo que depende de otros modelos
            Invoice.objects.all().delete()   # las facturas dependen de ventas
            Sale.objects.all().delete()      # las ventas dependen de bonos y pacientes
            Bonus.objects.all().delete()     # los bonos dependen de pacientes
            Patient.objects.all().delete()
            self.stdout.write(self.style.WARNING('   Datos borrados.'))

        # ── PASO 1: verificar que existen fisioterapeutas ─────────────────
        fisios = list(Physio.objects.filter(is_active=True))
        if not fisios:
            self.stdout.write(self.style.ERROR(
                '❌ No hay fisioterapeutas activos en la base de datos.\n'
                '   Crea al menos uno desde el admin antes de ejecutar este comando.'
            ))
            return

        self.stdout.write(f'✅ Fisioterapeutas encontrados: {len(fisios)}')

        # ── PASO 2: crear pacientes ───────────────────────────────────────
        num_pacientes = options['pacientes']
        self.stdout.write(f'\n👥 Creando {num_pacientes} pacientes...')

        pacientes_creados = []
        dni_usados = set()

        for i in range(num_pacientes):
            # Generamos un DNI único
            dni = generar_dni()
            intentos = 0
            while dni in dni_usados or Patient.objects.filter(dni=dni).exists():
                dni = generar_dni()
                intentos += 1
                if intentos > 50:
                    self.stdout.write(self.style.WARNING(
                        f'   ⚠️  No se pudo generar DNI único para paciente {i+1}'
                    ))
                    break
            dni_usados.add(dni)

            nombre = random.choice(NOMBRES)
            apellido1 = random.choice(APELLIDOS)
            apellido2 = random.choice(APELLIDOS)
            apellidos = f'{apellido1} {apellido2}'

            paciente = Patient.objects.create(
                dni=dni,
                first_name=nombre,
                last_name=apellidos,
                birth_date=generar_fecha_nacimiento(),
                phone=generar_telefono(),
                # usamos limpiar_texto() para evitar tildes en el email
                email=f'{limpiar_texto(nombre)}.{limpiar_texto(apellido1)}@email.com',
                is_active=True,
            )
            pacientes_creados.append(paciente)

        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(pacientes_creados)} pacientes creados'))

        # ── PASO 3: crear bonos ───────────────────────────────────────────
        num_bonos = options['bonos']
        self.stdout.write(f'\n🎫 Creando {num_bonos} bonos...')

        bonos_creados = []

        for _ in range(num_bonos):
            paciente = random.choice(pacientes_creados)
            tipo = random.choice([Bonus.BonusType.FIVE, Bonus.BonusType.TEN])

            bono = Bonus.objects.create(
                patient=paciente,
                bonus_type=tipo,
            )
            bonos_creados.append(bono)

        self.stdout.write(self.style.SUCCESS(f'   ✅ {len(bonos_creados)} bonos creados'))

        # ── PASO 4: crear ventas ──────────────────────────────────────────
        num_ventas = options['ventas']
        self.stdout.write(f'\n💰 Creando {num_ventas} ventas...')

        tipos_tratamiento = [t[0] for t in Sale.TreatmentType.choices]
        metodos_pago = [m[0] for m in Sale.PaymentMethod.choices]
        importes = [25, 30, 35, 40, 45, 50, 55, 60]

        ventas_creadas = 0

        for _ in range(num_ventas):
            paciente = random.choice(pacientes_creados)
            fisio = random.choice(fisios)
            tipo = random.choice(tipos_tratamiento)
            metodo = random.choice(metodos_pago)
            importe = random.choice(importes)
            fecha = generar_fecha_reciente(meses_atras=6)

            # El 30% de las ventas son de bono
            es_bono = random.random() < 0.30
            bono_asignado = None

            if es_bono:
                bonos_activos = Bonus.objects.filter(patient=paciente, is_active=True)
                if bonos_activos.exists():
                    bono_asignado = random.choice(list(bonos_activos))
                else:
                    es_bono = False

            # El 40% de las ventas tiene factura emitida
            tiene_factura = random.random() < 0.40

            try:
                sale = Sale.objects.create(
                    date=fecha,
                    patient=paciente,
                    amount=importe,
                    is_bonus=es_bono,
                    bonus=bono_asignado,
                    payment_method=metodo,
                    worker=fisio,
                    treatment_type=tipo,
                    invoice_issued=tiene_factura,
                    description='',
                )
                ventas_creadas += 1

                # ── NUEVO: crear el objeto Invoice si la venta tiene factura ──
                # Antes este paso no existía, lo que causaba errores 404
                # al intentar ver la factura desde el detalle de la venta
                if tiene_factura:
                    # Generamos el número usando el método estático del modelo
                    numero = Invoice.generate_number(fecha.year)

                    Invoice.objects.create(
                        sale=sale,
                        number=numero,
                        recipient_email=paciente.email,
                        issued_at=fecha,
                        # Cuerpo pre-rellenado con los datos de la venta
                        # igual que hace la vista invoice_create
                        body=(
                            f"Paciente: {paciente.full_name}\n"
                            f"DNI: {paciente.dni}\n\n"
                            f"Concepto: {sale.get_treatment_type_display()}\n"
                            f"Fecha de la sesión: {fecha.strftime('%d/%m/%Y')}\n\n"
                            f"Importe: {importe}€\n"
                            f"Método de pago: {sale.get_payment_method_display()}\n"
                        ),
                    )

            except Exception as e:
                self.stdout.write(self.style.WARNING(f'   ⚠️  Venta omitida: {e}'))

        self.stdout.write(self.style.SUCCESS(f'   ✅ {ventas_creadas} ventas creadas'))

        # ── RESUMEN FINAL ─────────────────────────────────────────────────
        self.stdout.write('\n' + '─' * 40)
        self.stdout.write(self.style.SUCCESS('🎉 Datos de prueba generados correctamente'))
        self.stdout.write(f'   Pacientes:  {Patient.objects.count()}')
        self.stdout.write(f'   Bonos:      {Bonus.objects.count()}')
        self.stdout.write(f'   Ventas:     {Sale.objects.count()}')
        self.stdout.write(f'   Facturas:   {Invoice.objects.count()}')
        self.stdout.write('─' * 40)