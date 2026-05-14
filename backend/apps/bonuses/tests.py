# backend/apps/bonuses/tests.py
# Tests del módulo de bonos.
# Verifican la lógica de sesiones y desactivación automática.

from django.test import TestCase
from apps.patients.models import Patient
from apps.users.models import Physio
from apps.bonuses.models import Bonus
from apps.sales.models import Sale
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model


class BonusModelTest(TestCase):
    """
    Tests de la lógica interna del modelo Bonus.
    No necesitamos login porque testamos el modelo directamente,
    no vistas que requieran autenticación.
    """

    def setUp(self):
        """Crea un paciente y un fisio reutilizables en todos los tests."""

        self.patient = Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
        )

        self.fisio = Physio.objects.create(
            first_name='David',
            last_name='Pachone',
            color='#2596be',
            is_active=True
        )

    def _crear_venta_de_bono(self, bono):
        """
        Método auxiliar privado — crea una venta asociada a un bono.
        El prefijo _ indica que es de uso interno en los tests.
        Evita repetir el mismo bloque en varios tests.
        """
        return Sale.objects.create(
            patient=self.patient,
            worker=self.fisio,
            amount=35,
            payment_method='efectivo',
            treatment_type='general',
            invoice_issued=False,
            is_bonus=True,
            bonus=bono,
        )

    # ── TESTS DE CREACIÓN ────────────────────────────────────────────

    def test_bono_nuevo_empieza_con_cero_sesiones_usadas(self):
        """Un bono recién creado no tiene ninguna sesión consumida."""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        self.assertEqual(bono.sessions_used, 0)

    def test_bono_cinco_sesiones_tiene_cinco_restantes_al_crear(self):
        """Un bono de 5 sesiones empieza con 5 disponibles."""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        self.assertEqual(bono.sessions_remaining, 5)

    def test_bono_diez_sesiones_tiene_diez_restantes_al_crear(self):
        """Un bono de 10 sesiones empieza con 10 disponibles."""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.TEN
        )

        self.assertEqual(bono.sessions_remaining, 10)

    def test_bono_nuevo_esta_activo(self):
        """Un bono recién creado debe estar activo."""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        self.assertTrue(bono.is_active)

    def test_bono_genera_numero_automaticamente(self):
        """Al crear un bono, se genera el número automáticamente (B001, B002...)"""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        # El número debe empezar con B y tener dígitos después
        self.assertTrue(bono.bonus_number.startswith('B'))
        self.assertTrue(bono.bonus_number[1:].isdigit())

    # ── TESTS DE CONSUMO DE SESIONES ────────────────────────────────

    def test_venta_de_bono_descuenta_una_sesion(self):
        """
        Al registrar una venta asociada a un bono,
        las sesiones usadas aumentan en 1.
        """

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        self._crear_venta_de_bono(bono)

        # Recargamos el bono desde la base de datos
        # sin esto, Python sigue viendo el objeto en memoria sin el cambio
        bono.refresh_from_db()

        self.assertEqual(bono.sessions_used, 1)
        self.assertEqual(bono.sessions_remaining, 4)

    def test_dos_ventas_descuentan_dos_sesiones(self):
        """Dos ventas de bono descuentan 2 sesiones."""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        self._crear_venta_de_bono(bono)
        self._crear_venta_de_bono(bono)

        bono.refresh_from_db()

        self.assertEqual(bono.sessions_used, 2)
        self.assertEqual(bono.sessions_remaining, 3)

    # ── TESTS DE DESACTIVACIÓN ───────────────────────────────────────

    def test_bono_se_desactiva_al_agotar_sesiones(self):
        """
        Al consumir todas las sesiones del bono,
        el bono se desactiva automáticamente.
        """

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        # Consumimos las 5 sesiones
        for _ in range(5):
            self._crear_venta_de_bono(bono)

        bono.refresh_from_db()

        self.assertFalse(bono.is_active)
        self.assertEqual(bono.sessions_used, 5)
        self.assertEqual(bono.sessions_remaining, 0)

    def test_bono_sigue_activo_con_sesiones_restantes(self):
        """Un bono con sesiones restantes debe seguir activo."""

        bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.FIVE
        )

        # Consumimos solo 4 de 5
        for _ in range(4):
            self._crear_venta_de_bono(bono)

        bono.refresh_from_db()

        self.assertTrue(bono.is_active)
        self.assertEqual(bono.sessions_remaining, 1)


User = get_user_model()


class BonusViewTest(TestCase):
    """
    Tests de las vistas del módulo de bonos.
    Verifican que las páginas responden correctamente
    y que el control de acceso funciona.
    """

    def setUp(self):
        """
        Prepara usuario, paciente y fisio reutilizables.
        También hace login para que los tests no fallen por falta de autenticación.
        """
        self.user = User.objects.create_user(
            username='test_bonus_view',
            email='bonus_view@clinicasolaz.com',
            password='test_password_123',
            first_name='Test',
            last_name='Usuario',
        )
        self.client = Client()
        self.client.login(
            username='bonus_view@clinicasolaz.com',
            password='test_password_123',
        )

        self.fisio = Physio.objects.create(
            first_name='Ana',
            last_name='Torres',
            color='#abcdef',
            is_active=True,
        )

        self.patient = Patient.objects.create(
            dni='99887766E',
            first_name='Sofía',
            last_name='Navarro Gil',
        )

        # Bono de prueba reutilizable
        self.bono = Bonus.objects.create(
            patient=self.patient,
            bonus_type=Bonus.BonusType.TEN,
        )

    # ── TESTS DE bonus_list ───────────────────────────────────────────

    def test_listado_bonos_devuelve_200(self):
        """La página de listado de bonos debe responder 200."""
        response = self.client.get(reverse('bonuses:list'))
        self.assertEqual(response.status_code, 200)

    def test_listado_sin_login_redirige_a_login(self):
        """Sin autenticación, el listado redirige a la página de login."""
        cliente_sin_login = Client()
        response = cliente_sin_login.get(reverse('bonuses:list'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_buscador_filtra_por_nombre_paciente(self):
        """
        El buscador debe devolver solo los bonos del paciente
        que coincide con el término de búsqueda.
        """
        # Creamos un segundo paciente con un bono — no debe aparecer en la búsqueda
        otro_paciente = Patient.objects.create(
            dni='11223355F',
            first_name='Roberto',
            last_name='Díaz Muñoz',
        )
        Bonus.objects.create(
            patient=otro_paciente,
            bonus_type=Bonus.BonusType.FIVE,
        )

        # Buscamos solo por 'Sofía' — debe aparecer solo el bono de Sofía
        response = self.client.get(reverse('bonuses:list') + '?q=Sofía')

        bonos_en_respuesta = list(response.context['bonuses'])

        self.assertEqual(len(bonos_en_respuesta), 1)
        self.assertEqual(bonos_en_respuesta[0].patient.first_name, 'Sofía')

    def test_buscador_sin_tildes_encuentra_paciente_con_tildes(self):
        """
        Buscar 'Sofia' (sin tilde) debe encontrar a 'Sofía' (con tilde).
        Verifica que la normalización de tildes funciona correctamente.
        """
        response = self.client.get(reverse('bonuses:list') + '?q=Sofia')
        bonos_en_respuesta = list(response.context['bonuses'])

        self.assertEqual(len(bonos_en_respuesta), 1)
        self.assertEqual(bonos_en_respuesta[0].patient.first_name, 'Sofía')

    # ── TESTS DE bonus_detail ─────────────────────────────────────────

    def test_detalle_bono_devuelve_200(self):
        """La página de detalle de un bono debe responder 200."""
        response = self.client.get(
            reverse('bonuses:detail', args=[self.bono.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_detalle_bono_inexistente_devuelve_404(self):
        """Pedir el detalle de un bono que no existe debe devolver 404."""
        response = self.client.get(
            reverse('bonuses:detail', args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_detalle_sin_login_redirige_a_login(self):
        """Sin autenticación, el detalle redirige al login."""
        cliente_sin_login = Client()
        response = cliente_sin_login.get(
            reverse('bonuses:detail', args=[self.bono.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    # ── TESTS DE bonus_create ─────────────────────────────────────────

    def test_crear_bono_get_devuelve_200(self):
        """La página del formulario de nuevo bono debe responder 200."""
        response = self.client.get(reverse('bonuses:create'))
        self.assertEqual(response.status_code, 200)

    def test_crear_bono_post_guarda_y_redirige(self):
        """
        Un POST válido debe crear el bono en la base de datos
        y redirigir al listado de bonos.
        """
        bonos_antes = Bonus.objects.count()

        response = self.client.post(reverse('bonuses:create'), {
            'patient': self.patient.pk,
            'bonus_type': Bonus.BonusType.FIVE,
        })

        # Debe redirigir al listado tras guardar
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('bonuses:list'))

        # Debe haber un bono más que antes
        self.assertEqual(Bonus.objects.count(), bonos_antes + 1)

    def test_crear_bono_post_genera_numero_automaticamente(self):
        """
        El bono creado por la vista debe tener número generado automáticamente.
        Verifica que el flujo completo vista → modelo funciona.
        """
        self.client.post(reverse('bonuses:create'), {
            'patient': self.patient.pk,
            'bonus_type': Bonus.BonusType.TEN,
        })

        # Buscamos el bono recién creado — el más reciente del paciente
        bono_nuevo = Bonus.objects.filter(patient=self.patient).order_by('-id').first()

        self.assertTrue(bono_nuevo.bonus_number.startswith('B'))
        self.assertTrue(bono_nuevo.bonus_number[1:].isdigit())

    def test_crear_bono_sin_login_redirige_a_login(self):
        """Sin autenticación, intentar crear un bono redirige al login."""
        cliente_sin_login = Client()
        response = cliente_sin_login.post(reverse('bonuses:create'), {
            'patient': self.patient.pk,
            'bonus_type': Bonus.BonusType.FIVE,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])