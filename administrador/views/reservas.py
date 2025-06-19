from django.shortcuts import render
from administrador.decorators import admin_required
from reservas.models import Reserva # Asume que tu modelo Reserva está en la app 'reservas'
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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