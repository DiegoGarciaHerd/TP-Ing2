# Sistema de Pagos con Tarjeta - Documentación

## Descripción General

Se ha implementado un sistema de pagos con tarjeta de crédito sencillo para el sistema de reservas de vehículos. El sistema simula el procesamiento de pagos y almacena la información necesaria para el seguimiento de transacciones.

## Flujo de Reserva y Pago

### 1. Flujo Completo
1. **Crear Reserva** (`/reservas/crear/<vehiculo_id>/`)
   - El usuario selecciona fechas de recogida y devolución
   - Se valida disponibilidad del vehículo
   - Se calcula el costo total
   - Se guarda información temporal en la sesión

2. **Ticket de Reserva** (`/reservas/ticket/<vehiculo_id>/`)
   - Muestra resumen de la reserva
   - Botón "Proceder al Pago"

3. **Procesar Pago** (`/reservas/pagar/<vehiculo_id>/`)
   - Formulario de tarjeta de crédito
   - Validación de datos de tarjeta (algoritmo de Luhn)
   - Simulación de procesamiento de pago
   - Tasa de éxito del 95% (para demostración)

4. **Confirmar Reserva** (`/reservas/confirmar/<vehiculo_id>/`)
   - Muestra resumen final con información de pago
   - Botón "Confirmar Reserva"

5. **Reserva Confirmada**
   - Página de éxito con todos los detalles
   - Información de pago y referencia de transacción

## Características del Sistema de Pagos

### Validaciones de Tarjeta
- **Número de tarjeta**: Algoritmo de Luhn para validación
- **Longitud**: Entre 13 y 19 dígitos
- **CVV**: 3 o 4 dígitos numéricos
- **Fecha de vencimiento**: No puede estar vencida
- **Formato**: Auto-formateo del número de tarjeta (espacios cada 4 dígitos)

### Información Almacenada
- Estado de pago (PENDIENTE, PROCESANDO, PAGADO, FALLIDO, REEMBOLSADO)
- Fecha y hora del pago
- Referencia única de transacción
- Últimos 4 dígitos de la tarjeta (para identificación)

### Seguridad
- No se almacena información completa de la tarjeta
- Solo se guardan los últimos 4 dígitos
- Referencia única para cada transacción
- Validación de sesión para evitar manipulación

## Modelos de Base de Datos

### Campos Agregados al Modelo `Reserva`
```python
# Campos de pago
estado_pago = models.CharField(max_length=20, choices=ESTADO_PAGO_CHOICES, default='PENDIENTE')
fecha_pago = models.DateTimeField(null=True, blank=True)
referencia_pago = models.CharField(max_length=100, null=True, blank=True)
ultimos_4_digitos_tarjeta = models.CharField(max_length=4, null=True, blank=True)
```

### Estados de Pago
- **PENDIENTE**: Pago no iniciado
- **PROCESANDO**: Pago en proceso
- **PAGADO**: Pago exitoso
- **FALLIDO**: Pago rechazado
- **REEMBOLSADO**: Pago reembolsado

## Archivos Modificados/Creados

### Modelos
- `reservas/models.py`: Agregados campos de pago

### Formularios
- `reservas/forms.py`: Agregado `PagoForm` con validaciones

### Vistas
- `reservas/views.py`: 
  - `procesar_pago()`: Nueva vista para procesar pagos
  - `confirmar_reserva()`: Modificada para incluir información de pago

### Templates
- `reservas/templates/reservas/procesar_pago.html`: Formulario de pago
- `reservas/templates/reservas/confirmar_reserva_final.html`: Confirmación final
- `reservas/templates/reservas/reserva_confirmada.html`: Página de éxito
- `reservas/templates/reservas/ticket_reserva.html`: Modificado para redirigir a pago
- `reservas/templates/reservas/mis_reservas.html`: Agregada información de pago

### URLs
- `reservas/urls.py`: Agregada ruta `pagar/<int:vehiculo_id>/`

### Utilidades
- `reservas/utils.py`: Función `procesar_pago_tarjeta()` para simular procesamiento

## Simulación de Procesamiento

El sistema simula un procesador de pagos real con:
- Delay de 1 segundo para simular comunicación con banco
- Tasa de éxito del 95%
- Generación de referencia única
- Diferentes tipos de errores simulados

### Tarjetas de Prueba
Para pruebas, puede usar estos números de tarjeta válidos (algoritmo de Luhn):
- `4532015112830366` (Visa)
- `5555555555554444` (MasterCard)
- `4000000000000002` (Visa - para simular errores ocasionales)

## Instalación y Configuración

### 1. Aplicar Migraciones
```bash
python manage.py makemigrations reservas
python manage.py migrate
```

### 2. Dependencias
No se requieren dependencias adicionales. El sistema usa solo Django y bibliotecas estándar de Python.

### 3. Configuración
El sistema está listo para usar sin configuración adicional. Para un entorno de producción, se recomienda:
- Integrar con un procesador de pagos real (Stripe, PayPal, etc.)
- Implementar logging de transacciones
- Agregar notificaciones por email
- Implementar webhooks para confirmaciones

## Uso en Producción

Para usar en producción, reemplace la función `procesar_pago_tarjeta()` en `utils.py` con una integración real a un procesador de pagos como:

### Stripe
```python
import stripe

def procesar_pago_tarjeta(numero_tarjeta, nombre_titular, mes_vencimiento, ano_vencimiento, cvv, monto):
    try:
        # Crear token de tarjeta
        token = stripe.Token.create(
            card={
                'number': numero_tarjeta,
                'exp_month': mes_vencimiento,
                'exp_year': ano_vencimiento,
                'cvc': cvv,
            }
        )
        
        # Procesar pago
        charge = stripe.Charge.create(
            amount=int(monto * 100),  # Stripe usa centavos
            currency='usd',
            source=token['id'],
            description='Reserva de vehículo'
        )
        
        return {
            'exito': True,
            'referencia_pago': charge['id'],
            'ultimos_4_digitos': charge['source']['last4'],
            'fecha_procesamiento': timezone.now(),
            'monto_procesado': monto,
            'mensaje': 'Pago procesado exitosamente'
        }
    except stripe.error.CardError as e:
        return {
            'exito': False,
            'codigo_error': e.code,
            'mensaje': e.user_message,
            'fecha_procesamiento': timezone.now()
        }
```

## Características de Seguridad Implementadas

1. **Validación de sesión**: Verificación de datos temporales
2. **Validación de formularios**: Algoritmo de Luhn y validaciones de fecha
3. **No almacenamiento de datos sensibles**: Solo últimos 4 dígitos
4. **Tokens CSRF**: Protección contra ataques CSRF
5. **Verificación de disponibilidad**: Re-verificación antes de confirmar

## Próximas Mejoras Sugeridas

1. **Notificaciones por email**: Confirmación de reserva y pago
2. **Reembolsos**: Sistema para procesar cancelaciones
3. **Múltiples métodos de pago**: PayPal, transferencias, etc.
4. **Facturación**: Generación de facturas PDF
5. **Historial de pagos**: Panel de administración para transacciones
6. **Webhooks**: Para confirmaciones asíncronas
7. **Logging avanzado**: Para auditoría y debugging 