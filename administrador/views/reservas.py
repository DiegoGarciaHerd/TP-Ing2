from django.shortcuts import render
from administrador.decorators import admin_required
from reservas.models import Reserva # Asume que tu modelo Reserva está en la app 'reservas'
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Count, Q
from datetime import datetime
from decimal import Decimal

@admin_required
def detalle_ingresos_reservas(request):

   # reservas_con_ingreso = Reserva.objects.filter(
   #     estado='COMPLETADA' 
  #  ).order_by('-fecha_creacion') 

    reservas_con_ingreso = Reserva.objects.all().order_by('-fecha_creacion')


    paginator = Paginator(reservas_con_ingreso, 10) 
    page = request.GET.get('page')

    try:
        reservas = paginator.page(page)
    except PageNotAnInteger:
        reservas = paginator.page(1)
    except EmptyPage:
        reservas = paginator.page(paginator.num_pages)

    context = {
        'reservas': reservas,
        'is_paginated': reservas.has_other_pages,
        'page_obj': reservas,
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
            estadisticas[key]['porcentaje'] = round((estadisticas[key]['cantidad'] / total_reservas) * 100)
    
    # Calcular ingresos por adicional
    for reserva in queryset:
        dias = (reserva.fecha_devolucion - reserva.fecha_recogida).days
        if dias <= 0:
            dias = 1
            
        if reserva.silla_para_ninos:
            estadisticas['silla_para_ninos']['ingresos'] += Decimal('1000.00') * dias
        if reserva.telepass:
            estadisticas['telepass']['ingresos'] += Decimal('2000.00') * dias
        if reserva.seguro_por_danos:
            estadisticas['seguro_por_danos']['ingresos'] += reserva.costo_base * Decimal('0.30')
        if reserva.conductor_adicional:
            estadisticas['conductor_adicional']['ingresos'] += reserva.costo_base * Decimal('0.20')
    
    # Calcular promedios por adicional
    for key in estadisticas:
        if estadisticas[key]['cantidad'] > 0:
            estadisticas[key]['promedio'] = estadisticas[key]['ingresos'] / estadisticas[key]['cantidad']
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
        'porcentaje_con_adicionales': round((reservas_con_adicionales / total_reservas) * 100) if total_reservas > 0 else 0,
        'filtros': {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'estado': estado
        },
        'estados_disponibles': Reserva.ESTADO_RESERVA_CHOICES
    }
    
    return render(request, 'administrador/estadisticas_adicionales.html', context)