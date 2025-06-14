from django.contrib import admin
from .models import AdminBalance

@admin.register(AdminBalance)
class AdminBalanceAdmin(admin.ModelAdmin):
    list_display = ('saldo',) 
    def has_add_permission(self, request):
        return False if AdminBalance.objects.exists() else True