# backend/apps/users/tests.py
# Tests del módulo de usuarios.
# Verifican autenticación, login, logout y control de acceso.

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Tests del modelo User personalizado."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@clinicasolaz.com',
            password='test_password_123',
            first_name='David',
            last_name='Pachone',
        )

    def test_str_devuelve_nombre_y_email(self):
        """__str__ debe devolver 'Nombre Apellido (email)'."""
        self.assertEqual(
            str(self.user),
            'David Pachone (test@clinicasolaz.com)'
        )

    def test_rol_por_defecto_es_physio(self):
        """Un usuario nuevo tiene rol 'physio' por defecto."""
        self.assertEqual(self.user.role, User.Role.PHYSIO)

    def test_is_owner_false_para_physio(self):
        """is_owner debe ser False para un usuario con rol physio."""
        self.assertFalse(self.user.is_owner)

    def test_is_owner_true_para_owner(self):
        """is_owner debe ser True para un usuario con rol owner."""
        owner = User.objects.create_user(
            username='owner_user',
            email='owner@clinicasolaz.com',
            password='test_password_123',
            first_name='Ana',
            last_name='García',
            role=User.Role.OWNER,
        )
        self.assertTrue(owner.is_owner)

    def test_email_es_unico(self):
        """No se pueden crear dos usuarios con el mismo email."""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='otro_user',
                email='test@clinicasolaz.com',  # mismo email
                password='test_password_123',
                first_name='Pedro',
                last_name='López',
            )


class LoginViewTest(TestCase):
    """Tests de la vista de login."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@clinicasolaz.com',
            password='test_password_123',
            first_name='David',
            last_name='Pachone',
        )
        self.client = Client()
        self.url_login = reverse('users:login')

    def test_login_page_accesible_sin_autenticar(self):
        """La página de login debe ser accesible sin autenticación."""
        response = self.client.get(self.url_login)
        self.assertEqual(response.status_code, 200)

    def test_login_correcto_redirige_al_inicio(self):
        """
        Un login con credenciales correctas debe redirigir al inicio.
        El sistema usa EMAIL para autenticar, no username.
        """
        response = self.client.post(self.url_login, {
            'email': 'test@clinicasolaz.com',
            'password': 'test_password_123',
        })
        # 302 = redirección tras login exitoso
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/')

    def test_login_incorrecto_no_redirige(self):
        """Un login con contraseña incorrecta debe quedarse en el login."""
        response = self.client.post(self.url_login, {
            'email': 'test@clinicasolaz.com',
            'password': 'contraseña_incorrecta',
        })
        # 200 = se vuelve a mostrar el formulario con error
        self.assertEqual(response.status_code, 200)

    def test_login_incorrecto_muestra_mensaje_error(self):
        """Con credenciales incorrectas debe aparecer el mensaje de error."""
        response = self.client.post(self.url_login, {
            'email': 'test@clinicasolaz.com',
            'password': 'contraseña_incorrecta',
        })
        # Verificamos que el mensaje de error está en los mensajes de Django
        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)
        self.assertIn('incorrectos', str(messages[0]))

    def test_usuario_autenticado_redirige_desde_login(self):
        """Un usuario ya autenticado que visita /login/ debe ser redirigido."""
        # Hacemos login primero
        self.client.login(
            username='test@clinicasolaz.com',
            password='test_password_123'
        )
        response = self.client.get(self.url_login)
        # Debe redirigir — no tiene sentido mostrar el login a alguien que ya entró
        self.assertEqual(response.status_code, 302)


class LogoutViewTest(TestCase):
    """Tests de la vista de logout."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='test_user',
            email='test@clinicasolaz.com',
            password='test_password_123',
            first_name='David',
            last_name='Pachone',
        )
        self.client = Client()
        self.client.login(
            username='test@clinicasolaz.com',
            password='test_password_123'
        )

    def test_logout_redirige_a_login(self):
        """Hacer logout debe redirigir a la página de login."""
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])

    def test_logout_cierra_la_sesion(self):
        """Después del logout el usuario no debe estar autenticado."""
        self.client.get(reverse('users:logout'))

        # Intentamos acceder a una página protegida — debe redirigir al login
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response['Location'])