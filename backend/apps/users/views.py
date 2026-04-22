# backend/apps/users/views.py
# Vistas del módulo de usuarios.
# Cada función maneja una URL y devuelve una respuesta HTTP.

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    # Si el usuario ya está autenticado, lo mandamos al inicio
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        # Recogemos los datos del formulario
        email = request.POST.get('email')
        password = request.POST.get('password')

        # authenticate() comprueba si el email y contraseña son correctos
        # Devuelve el objeto User si son válidos, o None si no
        user = authenticate(request, username=email, password=password)

        if user is not None:
            # login() crea la sesión del usuario en el navegador
            login(request, user)
            # Redirigimos al inicio (más adelante será el dashboard)
            return redirect('/')
        else:
            # Si las credenciales son incorrectas, mostramos un error
            messages.error(request, 'Email o contraseña incorrectos.')

    # GET: mostramos el formulario vacío
    # POST fallido: mostramos el formulario con el mensaje de error
    return render(request, 'users/login.html')


def logout_view(request):
    # logout() elimina la sesión del usuario
    logout(request)
    return redirect('users:login')


@login_required  # este decorador redirige a LOGIN_URL si el usuario no está autenticado
def profile_view(request):
    # Por ahora solo mostramos la página de perfil
    # En el siguiente paso añadiremos el formulario de edición
    return render(request, 'users/profile.html')