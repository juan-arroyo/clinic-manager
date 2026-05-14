# backend/apps/patients/tests.py
# Tests del módulo de pacientes.
# Verifican el modelo y las vistas con autenticación.

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.patients.models import Patient

User = get_user_model()


class PatientModelTest(TestCase):
    """Tests de la lógica interna del modelo Patient."""

    def test_full_name_devuelve_nombre_completo(self):
        """La propiedad full_name debe devolver 'Nombre Apellidos'."""
        patient = Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
        )
        self.assertEqual(patient.full_name, 'Marta Gil García')

    def test_str_devuelve_apellidos_nombre(self):
        """__str__ debe devolver 'Apellidos, Nombre' — como en el admin."""
        patient = Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
        )
        self.assertEqual(str(patient), 'Gil García, Marta')

    def test_paciente_nuevo_esta_activo_por_defecto(self):
        """Un paciente recién creado debe estar activo."""
        patient = Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
        )
        self.assertTrue(patient.is_active)

    def test_dni_es_unico(self):
        """No se pueden crear dos pacientes con el mismo DNI."""
        Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
        )
        # Intentar crear otro paciente con el mismo DNI debe lanzar excepción
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Patient.objects.create(
                dni='12345678A',  # mismo DNI
                first_name='Pedro',
                last_name='López',
            )


class PatientViewTest(TestCase):
    """Tests de las vistas de pacientes — requieren autenticación."""

    def setUp(self):
        """Crea usuario, hace login y crea un paciente de prueba."""
        self.user = User.objects.create_user(
            username='test_user',
            email='test@clinicasolaz.com',
            password='test_password_123',
            first_name='Test',
            last_name='Usuario',
        )
        self.client = Client()
        self.client.login(
            username='test@clinicasolaz.com',
            password='test_password_123'
        )
        self.patient = Patient.objects.create(
            dni='12345678A',
            first_name='Marta',
            last_name='Gil García',
            phone='600000001',
        )

    def test_listado_pacientes_accesible(self):
        """La página de listado de pacientes devuelve 200."""
        response = self.client.get(reverse('patients:list'))
        self.assertEqual(response.status_code, 200)

    def test_detalle_paciente_accesible(self):
        """La página de detalle de un paciente devuelve 200."""
        response = self.client.get(
            reverse('patients:detail', args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 200)

    def test_detalle_paciente_inexistente_devuelve_404(self):
        """Pedir el detalle de un paciente que no existe devuelve 404."""
        response = self.client.get(
            reverse('patients:detail', args=[99999])
        )
        self.assertEqual(response.status_code, 404)

    def test_listado_sin_login_redirige_a_login(self):
        """Sin autenticación, el listado redirige a la página de login."""
        # Creamos un cliente sin login
        cliente_sin_login = Client()
        response = cliente_sin_login.get(reverse('patients:list'))
        # 302 = redirección
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_buscador_filtra_por_nombre(self):
        """
        El buscador debe devolver solo los pacientes que coincidan
        con el término de búsqueda.
        """
        # Creamos un segundo paciente que NO debe aparecer en la búsqueda
        Patient.objects.create(
            dni='87654321B',
            first_name='Pedro',
            last_name='Gutiérrez',
        )

        # Buscamos solo por 'Marta'
        response = self.client.get(reverse('patients:list') + '?q=Marta')

        # El contexto contiene el queryset de pacientes devuelto por la vista
        patients_en_respuesta = list(response.context['patients'])

        # Solo debe aparecer Marta, no Pedro
        self.assertEqual(len(patients_en_respuesta), 1)
        self.assertEqual(patients_en_respuesta[0].first_name, 'Marta')