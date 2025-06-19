from django.shortcuts import render
from administrador.decorators import admin_required
from reservas.models import Reserva # Asume que tu modelo Reserva está en la app 'reservas'
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Sum, Q # Importa Sum para agregaciones
from datetime import datetime
from decimal import Decimal

@admin_required
def detalle_ingresos_reservas(request):
    """
    Vista para mostrar el detalle de ingresos por reservas con filtros y resumen.
    """
    # 1. Obtener parámetros de filtro de la solicitud GET
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado', 'TODOS') # Por defecto a 'TODOS'

    # 2. Queryset base de todas las reservas
    queryset = Reserva.objects.all().select_related('cliente', 'vehiculo').order_by('-fecha_creacion')

    # 3. Aplicar filtros al queryset
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            # Filtramos por la fecha de creación de la reserva
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_inicio_obj)
        except ValueError:
            # Puedes añadir un mensaje de error si la fecha es inválida
            pass

    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            # Filtramos por la fecha de creación de la reserva
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_fin_obj)
        except ValueError:
            # Puedes añadir un mensaje de error si la fecha es inválida
            pass

    if estado != 'TODOS':
        queryset = queryset.filter(estado=estado)

    # 4. Calcular estadísticas de resumen sobre el queryset FILTRADO
    total_reservas = queryset.count()
    
    # Suma de 'costo_total' de las reservas filtradas
    # 'or Decimal('0.00')' asegura que el valor sea 0 si no hay reservas o el sum es None
    total_ingresos_brutos = queryset.aggregate(Sum('costo_total'))['costo_total__sum'] or Decimal('0.00')

    promedio_ingresos_por_reserva = Decimal('0.00')
    if total_reservas > 0:
        promedio_ingresos_por_reserva = total_ingresos_brutos / Decimal(total_reservas)

    # 5. Configurar la paginación para las reservas filtradas
    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page')

    try:
        reservas = paginator.page(page_number)
    except PageNotAnInteger:
        reservas = paginator.page(1)
    except EmptyPage:
        reservas = paginator.page(paginator.num_pages)

    # 6. Preparar los datos del contexto para el template
    context = {
        'reservas': reservas,
        'is_paginated': reservas.has_other_pages,
        'page_obj': reservas, # Objeto de página para la paginación
        'total_reservas': total_reservas,
        'total_ingresos_brutos': total_ingresos_brutos,
        'promedio_ingresos_por_reserva': promedio_ingresos_por_reserva,
        'filtros': { # Para que los filtros se mantengan en el formulario
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'estado': estado,
        },
        # Asegúrate de que Reserva.ESTADO_CHOICES esté definido en tu modelo de Reserva
        'estados_disponibles': Reserva.ESTADO_CHOICES if hasattr(Reserva, 'ESTADO_CHOICES') else [],
    }
    return render(request, 'administrador/detalle_ingresos_reservas.html', context)


@admin_required
def estadisticas_adicionales(request):
    """
    Vista para mostrar estadísticas de uso de adicionales en las reservas
    """
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    
    # Query base
    queryset = Reserva.objects.all()
    
    # Aplicar filtros
    if fecha_inicio:
        try:
            fecha_inicio_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_inicio_obj)
        except ValueError:
            pass
    
    if fecha_fin:
        try:
            fecha_fin_obj = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_fin_obj)
        except ValueError:
            pass
    
    if estado and estado != 'TODOS':
        queryset = queryset.filter(estado=estado)
    
    # Calcular estadísticas
    total_reservas = queryset.count()
    
    # Estadísticas por adicional
    estadisticas = {
        'silla_para_ninos': {
            'nombre': 'Silla para Niños',
            'cantidad': queryset.filter(silla_para_ninos=True).count(),
            'porcentaje': 0,
            'ingresos': Decimal('0.00')
        },
        'telepass': {
            'nombre': 'TelePase',
            'cantidad': queryset.filter(telepass=True).count(),
            'porcentaje': 0,
            'ingresos': Decimal('0.00')
        },
        'seguro_por_danos': {
            'nombre': 'Seguro por Daños',
            'cantidad': queryset.filter(seguro_por_danos=True).count(),
            'porcentaje': 0,
            'ingresos': Decimal('0.00')
        },
        'conductor_adicional': {
            'nombre': 'Conductor Adicional',
            'cantidad': queryset.filter(conductor_adicional=True).count(),
            'porcentaje': 0,
            'ingresos': Decimal('0.00')
        }
    }
    
    # Calcular porcentajes e ingresos
    if total_reservas > 0:
        for key in estadisticas:
            # Asegúrate de usar Decimal para la división para evitar problemas de precisión con floats
            estadisticas[key]['porcentaje'] = round((estadisticas[key]['cantidad'] / Decimal(total_reservas)) * 100)
    
    # Calcular ingresos por adicional
    for reserva in queryset:
        # Asegúrate de que fecha_devolucion y fecha_recogida sean objetos date o datetime
        # Asumiendo que quieres el número de días que duró la reserva para el cálculo diario de adicionales
        # Si estas fechas son de tipo DateTimeField, necesitarás .date()
        dias = (reserva.fecha_devolucion - reserva.fecha_recogida).days
        if dias <= 0: # Si la reserva dura 0 o menos días (ej. mismo día de recogida y devolución), cuenta como 1 día
            dias = 1
            
        if reserva.silla_para_ninos:
            estadisticas['silla_para_ninos']['ingresos'] += Decimal('1000.00') * dias
        if reserva.telepass:
            estadisticas['telepass']['ingresos'] += Decimal('2000.00') * dias
        if reserva.seguro_por_danos:
            # Asegúrate de que 'costo_base' sea un DecimalField en tu modelo
            estadisticas['seguro_por_danos']['ingresos'] += reserva.costo_base * Decimal('0.30')
        if reserva.conductor_adicional:
            # Asegúrate de que 'costo_base' sea un DecimalField en tu modelo
            estadisticas['conductor_adicional']['ingresos'] += reserva.costo_base * Decimal('0.20')
    
    # Calcular promedios por adicional
    for key in estadisticas:
        if estadisticas[key]['cantidad'] > 0:
            estadisticas[key]['promedio'] = estadisticas[key]['ingresos'] / Decimal(estadisticas[key]['cantidad'])
        else:
            estadisticas[key]['promedio'] = Decimal('0.00')
    
    # Estadísticas generales
    total_ingresos_adicionales = sum(stats['ingresos'] for stats in estadisticas.values())
    reservas_con_adicionales = queryset.filter(
        Q(silla_para_ninos=True) |
        Q(telepass=True) |
        Q(seguro_por_danos=True) |
        Q(conductor_adicional=True)
    ).count()
    
    context = {
        'estadisticas': estadisticas,
        'total_reservas': total_reservas,
        'total_ingresos_adicionales': total_ingresos_adicionales,
        'reservas_con_adicionales': reservas_con_adicionales,
        # Asegúrate de que la división se haga con Decimal
        'porcentaje_con_adicionales': round((reservas_con_adicionales / Decimal(total_reservas)) * 100) if total_reservas > 0 else 0,
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'estado': estado
        },
        # Asume que tienes un atributo ESTADO_CHOICES en tu modelo Reserva
        'estados_disponibles': Reserva.ESTADO_CHOICES if hasattr(Reserva, 'ESTADO_CHOICES') else []
    }
    
    return render(request, 'administrador/estadisticas_adicionales.html', context)