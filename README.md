# AutoRental - Sistema de Administración de Alquiler de Vehículos

## Descripción
AutoRental es una aplicación web desarrollada con Django que permite la gestión integral de una empresa de alquiler de vehículos. El sistema facilita la administración de la flota de vehículos, reservas, clientes y empleados.

## Características Principales
- **Gestión de Vehículos**: Registro, categorización y seguimiento del estado de los vehículos (disponible, reservado, en mantenimiento, alquilado)
- **Administración de Usuarios**: Registro y gestión de clientes y empleados
- **Gestión de Sucursales**: Administración de múltiples puntos de alquiler
- **Sistema de Reservas**: Proceso completo para la reserva y alquiler de vehículos

## Tecnologías Utilizadas
- Django 5.2
- SQLite (base de datos)
- Python 3
- HTML/CSS

## Instrucciones de Instalación

1. Clonar el repositorio
2. Crear y activar un entorno virtual:
   ```
   python -m venv venv
   venv\Scripts\activate  # En Windows
   ```
3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Aplicar las migraciones:
   ```
   python manage.py migrate
   ```
5. Ejecutar el servidor de desarrollo:
   ```
   python manage.py runserver
   ```

## Estructura del Proyecto
- **autorental**: Configuración principal del proyecto Django
- **home**: Aplicación para la página principal
- **usuarios**: Gestión de usuarios y autenticación
- **vehiculos**: Administración de la flota de vehículos
- **empleados**: Gestión del personal y sucursales 