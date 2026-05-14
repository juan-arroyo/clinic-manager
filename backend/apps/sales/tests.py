# backend/apps/sales/tests.py
# Tests del módulo de ventas.
# Verifican la lógica de generación de facturas y creación de ventas.

from django.test import TestCase
from django.utils import timezone
from apps.patients.models import Patient
from apps.users.models import Physio
from apps.bonuses.models import Bonus
from apps.sales.models import Sale, Invoice
from django.core import mail   # lo importamos aquí para no romper el orden del archivo
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse


class SaleModelTest(TestCase):
    """Tests de la lógica interna del modelo Sale."""

    def setUp(self):
        self.patient = Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
            email='marta@test.com',
        )
        self.fisio = Physio.objects.create(
            first_name='David',
            last_name='Pachone',
            color='#2596be',
            is_active=True
        )

    def _crear_venta(self, invoice_issued=False):
        """Método auxiliar — crea una venta básica."""
        return Sale.objects.create(
            patient=self.patient,
            worker=self.fisio,
            amount=35,
            payment_method='efectivo',
            treatment_type='general',
            invoice_issued=invoice_issued,
        )

    # ── TESTS DE CREACIÓN BÁSICA ─────────────────────────────────────

    def test_venta_sin_factura_no_genera_numero(self):
        """
        Una venta sin factura emitida no debe tener número de factura.
        invoice_number debe ser None.
        """
        venta = self._crear_venta(invoice_issued=False)
        self.assertIsNone(venta.invoice_number)

    def test_venta_con_factura_genera_numero(self):
        """
        Una venta con factura emitida debe tener número de factura generado.
        """
        venta = self._crear_venta(invoice_issued=True)
        self.assertIsNotNone(venta.invoice_number)

    def test_numero_factura_formato_correcto(self):
        """
        El número de factura debe tener el formato AÑO/NNN.
        Ejemplo: 2026/001
        """
        venta = self._crear_venta(invoice_issued=True)
        año_actual = str(timezone.localdate().year)

        # Debe empezar con el año actual
        self.assertTrue(venta.invoice_number.startswith(año_actual))

        # Debe contener una barra separadora
        self.assertIn('/', venta.invoice_number)

        # La parte después de la barra debe tener 3 dígitos (001, 002...)
        partes = venta.invoice_number.split('/')
        self.assertEqual(len(partes), 2)
        self.assertEqual(len(partes[1]), 3)
        self.assertTrue(partes[1].isdigit())

    def test_primera_factura_del_año_es_001(self):
        """La primera factura del año debe ser 2026/001, no 2026/000 ni 2026/002."""
        venta = self._crear_venta(invoice_issued=True)
        año_actual = str(timezone.localdate().year)

        self.assertEqual(venta.invoice_number, f'{año_actual}/001')

    def test_segunda_factura_del_año_es_002(self):
        """La segunda factura del año debe ser 2026/002."""
        self._crear_venta(invoice_issued=True)  # primera → 001
        venta2 = self._crear_venta(invoice_issued=True)  # segunda → 002

        año_actual = str(timezone.localdate().year)
        self.assertEqual(venta2.invoice_number, f'{año_actual}/002')

    def test_numeros_de_factura_son_unicos(self):
        """
        Dos ventas con factura no pueden tener el mismo número.
        Esto es crítico — dos facturas con el mismo número es un error contable.
        """
        venta1 = self._crear_venta(invoice_issued=True)
        venta2 = self._crear_venta(invoice_issued=True)

        self.assertNotEqual(venta1.invoice_number, venta2.invoice_number)


class InvoiceModelTest(TestCase):
    """Tests del modelo Invoice — la factura como documento separado."""

    def setUp(self):
        self.patient = Patient.objects.create(
            dni='87654321B',
            first_name='Pedro',
            last_name='Gutiérrez Gómez',
            email='pedro@test.com',
        )
        self.fisio = Physio.objects.create(
            first_name='Matias',
            last_name='Fermu',
            color='#ff5733',
            is_active=True
        )
        self.venta = Sale.objects.create(
            patient=self.patient,
            worker=self.fisio,
            amount=35,
            payment_method='efectivo',
            treatment_type='general',
            invoice_issued=False,
        )

    def test_generate_number_primera_factura(self):
        """Invoice.generate_number() debe devolver AÑO/001 si no hay facturas."""
        año = timezone.localdate().year
        numero = Invoice.generate_number(año)
        self.assertEqual(numero, f'{año}/001')

    def test_generate_number_incrementa_correctamente(self):
        """Después de crear una factura, la siguiente debe ser AÑO/002."""
        año = timezone.localdate().year

        # Creamos la primera factura
        Invoice.objects.create(
            sale=self.venta,
            number=Invoice.generate_number(año),
            recipient_email='pedro@test.com',
            body='Concepto de prueba',
            issued_at=timezone.localdate(),
        )

        # La siguiente debe ser /002
        numero_siguiente = Invoice.generate_number(año)
        self.assertEqual(numero_siguiente, f'{año}/002')

    def test_generate_number_formato_tres_digitos(self):
        """El número siempre debe tener 3 dígitos: 001, no 1."""
        año = timezone.localdate().year
        numero = Invoice.generate_number(año)
        partes = numero.split('/')
        self.assertEqual(len(partes[1]), 3)



# ─────────────────────────────────────────────────────────────────────────────
# TESTS DE ENVÍO DE EMAIL (invoice_send)
# ─────────────────────────────────────────────────────────────────────────────
# Durante los tests, Django NO envía emails reales.
# En su lugar, los guarda en django.core.mail.outbox (una lista en memoria).
# Podemos leer esa lista para verificar que el email se "habría enviado".



User = get_user_model()


class InvoiceSendTest(TestCase):
    """
    Tests de la vista invoice_send.
    Verifican que el email se prepara correctamente y que
    la base de datos se actualiza tras el envío.
    """

    def setUp(self):
        """
        Prepara todos los datos necesarios:
        usuario, paciente, fisio, venta y factura.
        """
        # Usuario de prueba para hacer login
        self.user = User.objects.create_user(
            username='test_send_user',
            email='test_send@clinicasolaz.com',
            password='test_password_123',
            first_name='Test',
            last_name='Usuario',
        )

        self.client = Client()
        self.client.login(
            username='test_send@clinicasolaz.com',
            password='test_password_123',
        )

        # Fisioterapeuta de prueba
        self.fisio = Physio.objects.create(
            first_name='David',
            last_name='Pachone',
            color='#2596be',
            is_active=True,
        )

        # Paciente con email — es el destinatario de la factura
        self.patient = Patient.objects.create(
            dni='11223344C',
            first_name='Laura',
            last_name='Blanco Serrano',
            email='laura@test.com',
        )

        # Venta base — sin factura todavía
        self.venta = Sale.objects.create(
            patient=self.patient,
            worker=self.fisio,
            amount=40,
            payment_method='efectivo',
            treatment_type='general',
            invoice_issued=False,
        )

        # Creamos la factura manualmente para poder testear el envío
        año = self.venta.date.year
        self.invoice = Invoice.objects.create(
            sale=self.venta,
            number=Invoice.generate_number(año),
            recipient_email='laura@test.com',
            body='Concepto: Sesión de fisioterapia general.\nImporte: 40€',
            issued_at=self.venta.date,
        )

    # ── TESTS DE MÉTODO HTTP ─────────────────────────────────────────

    def test_get_a_invoice_send_redirige_sin_enviar(self):
        """
        Una petición GET a invoice_send NO debe enviar el email.
        Solo se acepta POST — un GET redirige sin hacer nada.
        Esta protección evita envíos accidentales al navegar.
        """
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        response = self.client.get(url)

        # Debe redirigir — no procesar nada
        self.assertEqual(response.status_code, 302)

        # outbox es la bandeja de salida falsa de Django durante los tests
        # Debe estar vacía porque el GET no debería haber enviado nada
        self.assertEqual(len(mail.outbox), 0)

    # ── TESTS DE ENVÍO ────────────────────────────────────────────────

    def test_post_envia_exactamente_un_email(self):
        """
        Una petición POST válida debe enviar exactamente 1 email.
        """
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        self.client.post(url)

        # mail.outbox es una lista — debe tener exactamente 1 elemento
        self.assertEqual(len(mail.outbox), 1)

    def test_email_enviado_al_destinatario_correcto(self):
        """
        El email debe llegar al email guardado en la factura (recipient_email).
        """
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        self.client.post(url)

        email_enviado = mail.outbox[0]

        # mail.outbox[0].to es una lista de destinatarios
        self.assertIn('laura@test.com', email_enviado.to)

    def test_email_tiene_pdf_adjunto(self):
        """
        El email debe llevar adjunto un archivo PDF.
        Verificamos que hay al menos un adjunto y que es un PDF.
        """
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        self.client.post(url)

        email_enviado = mail.outbox[0]

        # attachments es una lista de tuplas: (nombre, contenido, tipo_mime)
        self.assertEqual(len(email_enviado.attachments), 1)

        nombre_adjunto, contenido_adjunto, tipo_mime = email_enviado.attachments[0]

        # El tipo MIME debe ser application/pdf
        self.assertEqual(tipo_mime, 'application/pdf')

        # El nombre del archivo debe contener el número de factura
        # El número tiene formato 2026/001 — en el nombre se reemplaza / por -
        numero_en_nombre = self.invoice.number.replace('/', '-')
        self.assertIn(numero_en_nombre, nombre_adjunto)

    def test_email_asunto_contiene_numero_factura(self):
        """
        El asunto del email debe incluir el número de factura.
        Así el paciente sabe de qué se trata sin abrir el adjunto.
        """
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        self.client.post(url)

        email_enviado = mail.outbox[0]

        self.assertIn(self.invoice.number, email_enviado.subject)

    # ── TESTS DE BASE DE DATOS ────────────────────────────────────────

    def test_last_sent_at_se_actualiza_tras_envio(self):
        """
        Después de enviar el email, invoice.last_sent_at debe
        tener una fecha y hora registrada (no debe ser None).
        Este campo sirve para saber cuándo se envió por última vez.
        """
        # Antes del envío debe ser None
        self.assertIsNone(self.invoice.last_sent_at)

        url = reverse('sales:invoice_send', args=[self.venta.pk])
        self.client.post(url)

        # Recargamos la factura desde la base de datos
        self.invoice.refresh_from_db()

        # Ahora debe tener una fecha
        self.assertIsNotNone(self.invoice.last_sent_at)

    def test_post_redirige_a_invoice_detail(self):
        """
        Tras enviar el email, la vista debe redirigir
        a la página de detalle de la factura.
        """
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        response = self.client.post(url)

        # 302 = redirección
        self.assertEqual(response.status_code, 302)

        # Debe redirigir al detalle de la factura de esta venta
        url_esperada = reverse('sales:invoice_detail', args=[self.venta.pk])
        self.assertEqual(response['Location'], url_esperada)

    # ── TEST DE SEGURIDAD ─────────────────────────────────────────────

    def test_sin_login_redirige_a_login(self):
        """
        Sin autenticación, invoice_send debe redirigir al login.
        No debe ser posible enviar facturas sin estar autenticado.
        """
        # Cliente sin login
        cliente_sin_login = Client()
        url = reverse('sales:invoice_send', args=[self.venta.pk])
        response = cliente_sin_login.post(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])



# ─────────────────────────────────────────────────────────────────────────────
# TESTS DE VISTAS DE FACTURA (invoice_create, invoice_edit, invoice_detail)
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceViewTest(TestCase):
    """
    Tests de las vistas que manejan el ciclo de vida de una factura:
    crear, ver detalle, editar y descargar el PDF.
    """

    def setUp(self):
        """
        Prepara usuario, paciente, fisio y venta reutilizables.
        La venta empieza SIN factura — cada test decide si la crea o no.
        """
        self.user = User.objects.create_user(
            username='test_invoice_view',
            email='invoice_view@clinicasolaz.com',
            password='test_password_123',
            first_name='Test',
            last_name='Usuario',
        )
        self.client = Client()
        self.client.login(
            username='invoice_view@clinicasolaz.com',
            password='test_password_123',
        )

        self.fisio = Physio.objects.create(
            first_name='Carlos',
            last_name='Ruiz',
            color='#123456',
            is_active=True,
        )

        self.patient = Patient.objects.create(
            dni='55667788D',
            first_name='Elena',
            last_name='Martínez López',
            email='elena@test.com',
        )

        # Venta sin factura — punto de partida limpio para cada test
        self.venta = Sale.objects.create(
            patient=self.patient,
            worker=self.fisio,
            amount=50,
            payment_method='tarjeta',
            treatment_type='general',
            invoice_issued=False,
        )

    def _crear_factura(self):
        """
        Método auxiliar privado — crea una factura para self.venta.
        Lo usamos en los tests que necesitan que la factura ya exista.
        El prefijo _ indica que es de uso interno en esta clase.
        """
        año = self.venta.date.year
        return Invoice.objects.create(
            sale=self.venta,
            number=Invoice.generate_number(año),
            recipient_email='elena@test.com',
            body='Concepto: Sesión general.\nImporte: 50€',
            issued_at=self.venta.date,
        )

    # ── TESTS DE invoice_create ───────────────────────────────────────

    def test_invoice_create_devuelve_200_si_no_hay_factura(self):
        """
        La página de crear factura debe responder 200
        cuando la venta todavía no tiene factura asociada.
        """
        url = reverse('sales:invoice_create', args=[self.venta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_invoice_create_redirige_si_ya_existe_factura(self):
        """
        Si la venta ya tiene factura, invoice_create debe redirigir
        al detalle de esa factura en lugar de mostrar el formulario.
        Evita crear facturas duplicadas para la misma venta.
        """
        self._crear_factura()  # creamos la factura primero

        url = reverse('sales:invoice_create', args=[self.venta.pk])
        response = self.client.get(url)

        # Debe redirigir — no mostrar el formulario de creación
        self.assertEqual(response.status_code, 302)

        url_esperada = reverse('sales:invoice_detail', args=[self.venta.pk])
        self.assertEqual(response['Location'], url_esperada)

    def test_invoice_create_post_crea_factura_y_redirige(self):
        """
        Un POST válido debe crear la factura en la base de datos
        y redirigir al detalle de la factura.
        """
        url = reverse('sales:invoice_create', args=[self.venta.pk])

        response = self.client.post(url, {
            'issued_at': self.venta.date.strftime('%Y-%m-%d'),
            'recipient_email': 'elena@test.com',
            'body': 'Concepto: Sesión general.\nImporte: 50€',
        })

        # Debe redirigir tras guardar
        self.assertEqual(response.status_code, 302)

        # La factura debe existir ahora en la base de datos
        self.assertTrue(Invoice.objects.filter(sale=self.venta).exists())

    def test_invoice_create_post_marca_venta_como_facturada(self):
        """
        Al crear la factura, la venta debe quedar marcada
        con invoice_issued=True automáticamente.
        """
        url = reverse('sales:invoice_create', args=[self.venta.pk])

        self.client.post(url, {
            'issued_at': self.venta.date.strftime('%Y-%m-%d'),
            'recipient_email': 'elena@test.com',
            'body': 'Concepto: Sesión general.\nImporte: 50€',
        })

        # Recargamos la venta desde la base de datos
        self.venta.refresh_from_db()

        self.assertTrue(self.venta.invoice_issued)
        # El número de factura también debe haberse guardado en la venta
        self.assertIsNotNone(self.venta.invoice_number)

    # ── TESTS DE invoice_detail ───────────────────────────────────────

    def test_invoice_detail_devuelve_200(self):
        """La página de detalle de factura debe responder 200."""
        self._crear_factura()

        url = reverse('sales:invoice_detail', args=[self.venta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_invoice_detail_devuelve_404_si_no_hay_factura(self):
        """
        Si la venta no tiene factura, el detalle debe devolver 404.
        No tiene sentido mostrar una página de factura vacía.
        """
        # No llamamos a _crear_factura() — la venta no tiene factura
        url = reverse('sales:invoice_detail', args=[self.venta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_invoice_detail_sin_login_redirige(self):
        """Sin autenticación, el detalle de factura redirige al login."""
        self._crear_factura()

        cliente_sin_login = Client()
        url = reverse('sales:invoice_detail', args=[self.venta.pk])
        response = cliente_sin_login.get(url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    # ── TESTS DE invoice_edit ─────────────────────────────────────────

    def test_invoice_edit_devuelve_200(self):
        """La página de editar factura debe responder 200."""
        self._crear_factura()

        url = reverse('sales:invoice_edit', args=[self.venta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_invoice_edit_post_actualiza_datos(self):
        """
        Un POST válido a invoice_edit debe guardar los cambios
        en la base de datos y redirigir al detalle.
        """
        factura = self._crear_factura()

        url = reverse('sales:invoice_edit', args=[self.venta.pk])
        response = self.client.post(url, {
            'issued_at': self.venta.date.strftime('%Y-%m-%d'),
            'recipient_email': 'nuevo_email@test.com',  # cambiamos el email
            'body': 'Cuerpo modificado.',
        })

        # Debe redirigir tras guardar
        self.assertEqual(response.status_code, 302)

        # Recargamos la factura y verificamos que el email cambió
        factura.refresh_from_db()
        self.assertEqual(factura.recipient_email, 'nuevo_email@test.com')

    # ── TESTS DE generate_invoice_pdf ────────────────────────────────

    def test_pdf_devuelve_200(self):
        """La vista de descarga de PDF debe responder 200."""
        self._crear_factura()

        url = reverse('sales:invoice_pdf', args=[self.venta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_pdf_content_type_es_pdf(self):
        """
        La respuesta del PDF debe tener Content-Type application/pdf.
        Esto le dice al navegador que debe descargarlo como PDF.
        """
        self._crear_factura()

        url = reverse('sales:invoice_pdf', args=[self.venta.pk])
        response = self.client.get(url)

        self.assertIn('application/pdf', response['Content-Type'])

    def test_pdf_devuelve_404_si_no_hay_factura(self):
        """
        Si la venta no tiene factura, pedir el PDF debe devolver 404.
        No se puede generar un PDF de una factura que no existe.
        """
        # No creamos factura
        url = reverse('sales:invoice_pdf', args=[self.venta.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)