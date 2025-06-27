from django.shortcuts import render
from administrador.decorators import admin_required
from reservas.models import Reserva
from vehiculos.models import Vehiculo
from django.db.models import Count, Avg, Sum, Q, F
from datetime import datetime, timedelta
from decimal import Decimal

@admin_required
def estadisticas_autos(request):
    """
    Vista para mostrar estadísticas específicas de autos/vehículos
    """
    # Obtener parámetros de filtro
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    tipo_vehiculo = request.GET.get('tipo_vehiculo')
    
    # Query base
    queryset = Reserva.objects.all().select_related('vehiculo', 'cliente')
    
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
    
    if tipo_vehiculo and tipo_vehiculo != 'TODOS':
        queryset = queryset.filter(vehiculo__tipo=tipo_vehiculo)
    
    # 1. Autos más reservados
    autos_mas_reservados = queryset.values(
        'vehiculo__marca', 
        'vehiculo__modelo', 
        'vehiculo__patente',
        'vehiculo__tipo'
    ).annotate(
        total_reservas=Count('id'),
        reservas_confirmadas=Count('id', filter=Q(estado='CONFIRMADA')),
        reservas_canceladas=Count('id', filter=Q(estado='CANCELADA')),
        reservas_finalizadas=Count('id', filter=Q(estado='FINALIZADA'))
    ).order_by('-total_reservas')[:10]
    
    # 2. Días promedio por vehículo - Usando lógica compatible con SQLite
    dias_promedio_por_vehiculo = []
    vehiculos_con_reservas = queryset.values(
        'vehiculo__marca', 
        'vehiculo__modelo', 
        'vehiculo__patente'
    ).annotate(
        total_reservas=Count('id')
    ).filter(total_reservas__gt=0)
    
    for vehiculo_data in vehiculos_con_reservas:
        # Obtener todas las reservas para este vehículo
        reservas_vehiculo = queryset.filter(
            vehiculo__marca=vehiculo_data['vehiculo__marca'],
            vehiculo__modelo=vehiculo_data['vehiculo__modelo'],
            vehiculo__patente=vehiculo_data['vehiculo__patente']
        )
        
        dias_totales = 0
        for reserva in reservas_vehiculo:
            dias = (reserva.fecha_devolucion - reserva.fecha_recogida).days
            if dias <= 0:
                dias = 1
            dias_totales += dias
        
        dias_promedio = dias_totales / vehiculo_data['total_reservas'] if vehiculo_data['total_reservas'] > 0 else 0
        
        dias_promedio_por_vehiculo.append({
            'vehiculo__marca': vehiculo_data['vehiculo__marca'],
            'vehiculo__modelo': vehiculo_data['vehiculo__modelo'],
            'vehiculo__patente': vehiculo_data['vehiculo__patente'],
            'total_reservas': vehiculo_data['total_reservas'],
            'dias_promedio': dias_promedio,
            'dias_totales': dias_totales
        })
    
    # Ordenar por días totales y tomar los top 10
    dias_promedio_por_vehiculo.sort(key=lambda x: x['dias_totales'], reverse=True)
    dias_promedio_por_vehiculo = dias_promedio_por_vehiculo[:10]
    
    # 3. Autos con más cancelaciones
    autos_mas_cancelaciones = queryset.filter(estado='CANCELADA').values(
        'vehiculo__marca', 
        'vehiculo__modelo', 
        'vehiculo__patente'
    ).annotate(
        total_cancelaciones=Count('id')
    ).order_by('-total_cancelaciones')[:10]
    
    # Calcular porcentaje de cancelación para cada vehículo
    for auto in autos_mas_cancelaciones:
        total_reservas_vehiculo = queryset.filter(
            vehiculo__marca=auto['vehiculo__marca'],
            vehiculo__modelo=auto['vehiculo__modelo'],
            vehiculo__patente=auto['vehiculo__patente']
        ).count()
        auto['total_reservas'] = total_reservas_vehiculo
        auto['porcentaje_cancelacion'] = (auto['total_cancelaciones'] / total_reservas_vehiculo * 100) if total_reservas_vehiculo > 0 else 0
    
    # 4. Estadísticas de adicionales por vehículo
    estadisticas_adicionales_por_vehiculo = queryset.values(
        'vehiculo__marca', 
        'vehiculo__modelo', 
        'vehiculo__patente'
    ).annotate(
        total_reservas=Count('id'),
        silla_para_ninos_count=Count('id', filter=Q(silla_para_ninos=True)),
        telepass_count=Count('id', filter=Q(telepass=True)),
        seguro_por_danos_count=Count('id', filter=Q(seguro_por_danos=True)),
        conductor_adicional_count=Count('id', filter=Q(conductor_adicional=True)),
        total_adicionales=Count('id', filter=Q(
            Q(silla_para_ninos=True) | 
            Q(telepass=True) | 
            Q(seguro_por_danos=True) | 
            Q(conductor_adicional=True)
        )),
        ingresos_adicionales=Sum('monto_adicional')
    ).filter(total_reservas__gt=0).order_by('-total_adicionales')[:10]
    
    # 5. Vehículos más rentables (por ingresos totales)
    vehiculos_mas_rentables = queryset.values(
        'vehiculo__marca', 
        'vehiculo__modelo', 
        'vehiculo__patente',
        'vehiculo__precio_por_dia'
    ).annotate(
        total_reservas=Count('id'),
        ingresos_totales=Sum('costo_total'),
        ingresos_base=Sum('costo_base'),
        ingresos_adicionales=Sum('monto_adicional')
    ).filter(total_reservas__gt=0).order_by('-ingresos_totales')[:10]
    
    # Calcular días alquilados para cada vehículo
    for vehiculo in vehiculos_mas_rentables:
        reservas_vehiculo = queryset.filter(
            vehiculo__marca=vehiculo['vehiculo__marca'],
            vehiculo__modelo=vehiculo['vehiculo__modelo'],
            vehiculo__patente=vehiculo['vehiculo__patente']
        )
        dias_alquilados = 0
        for reserva in reservas_vehiculo:
            dias = (reserva.fecha_devolucion - reserva.fecha_recogida).days
            if dias <= 0:
                dias = 1
            dias_alquilados += dias
        vehiculo['dias_alquilados'] = dias_alquilados
    
    context = {
        'autos_mas_reservados': autos_mas_reservados,
        'dias_promedio_por_vehiculo': dias_promedio_por_vehiculo,
        'autos_mas_cancelaciones': autos_mas_cancelaciones,
        'estadisticas_adicionales_por_vehiculo': estadisticas_adicionales_por_vehiculo,
        'vehiculos_mas_rentables': vehiculos_mas_rentables,
        'total_reservas': queryset.count(),
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'estado': estado,
            'tipo_vehiculo': tipo_vehiculo
        },
        'estados_disponibles': Reserva.ESTADO_RESERVA_CHOICES,
        'tipos_vehiculo': Vehiculo.TIPO_CHOICES
    }
    
    return render(request, 'administrador/estadisticas_autos.html', context) 