from django.views.generic import ListView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count, Q
from vehiculos.models import Vehiculo
from sucursales.models import Sucursal
from django.utils import timezone

class AdminVehiculosListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Vehiculo
    template_name = 'administrador/listado_vehiculos.html'
    context_object_name = 'vehiculos'
    paginate_by = 10

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def get_queryset(self):
        queryset = Vehiculo.objects.all().select_related('sucursal_actual')
        
        # Agregar conteo de reservas activas
        queryset = queryset.annotate(
            reservas_activas_count=Count(
                'reservas',
                filter=Q(
                    reservas__estado__in=['PENDIENTE', 'CONFIRMADA'],
                    reservas__fecha_devolucion__gte=timezone.now().date()
                )
            )
        )

        # Aplicar filtros
        sucursal = self.request.GET.get('sucursal')
        estado = self.request.GET.get('estado')
        q = self.request.GET.get('q')

        if sucursal:
            queryset = queryset.filter(sucursal_actual_id=sucursal)
        if estado:
            if estado == 'disponible':
                queryset = queryset.filter(disponible=True)
            elif estado == 'no_disponible':
                queryset = queryset.filter(disponible=False)
        if q:
            queryset = queryset.filter(
                Q(marca__icontains=q) |
                Q(modelo__icontains=q) |
                Q(patente__icontains=q)
            )

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sucursales'] = Sucursal.objects.all()
        context['tipos_vehiculo'] = Vehiculo.TIPOS_VEHICULO
        return context 