# AutoRental - Sistema de Administración de Alquiler de Vehículos

## Descripción
AutoRental es una aplicación web desarrollada con Django que permite la gestión integral de una empresa de alquiler de vehículos. El sistema facilita la administración de la flota de vehículos, reservas, clientes y empleados.

## Características Principales
- **Gestión de Vehículos**: Registro, categorización y seguimiento del estado de los vehículos (disponible, reservado, en mantenimiento, alquilado)
- **Administración de Usuarios**: Registro y gestión de clientes y empleados
- **Gestión de Sucursales**: Administración de múltiples puntos de alquiler
- **Sistema de Reservas**: Proceso completo para la reserva y alquiler de vehículos
- **Sistema de Pagos**: Procesamiento seguro de pagos con tarjetas guardadas y validación de CVV

## Tecnologías Utilizadas
- Django 5.2
- SQLite (base de datos)
- Python 3
- HTML/CSS
- Cryptography (para encriptación de datos sensibles)

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
- **reservas**: Sistema de reservas y procesamiento de pagos

## Sistema de Pagos
El sistema incluye un módulo de procesamiento de pagos con las siguientes características:

### Tarjetas de Prueba
Para realizar pruebas en el sistema, se pueden utilizar las siguientes tarjetas:
- Tarjeta terminada en 1645 (4517660196851645) - CVV: 789
- Tarjeta terminada en 7961 (5258556802017961) - CVV: 345

### Seguridad
- Encriptación de números de tarjeta
- Almacenamiento seguro de solo los últimos 4 dígitos
- Validación de CVV para cada transacción
- Sin almacenamiento de CVV

### Flujo de Pago
1. El usuario guarda su tarjeta en el sistema
2. Al realizar una reserva, selecciona la tarjeta guardada
3. Ingresa el CVV para confirmar la transacción
4. El sistema valida los datos y procesa el pago
5. Se genera una referencia única de pago
6. Se envía confirmación por correo electrónico 