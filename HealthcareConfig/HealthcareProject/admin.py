from django.contrib import admin
from .models import Objet, Capteur, Actionneur, Mesure, Commande, Patient

admin.site.register([Objet, Capteur, Actionneur, Patient])


@admin.register(Mesure, Commande)
class HistoriqueAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False