from django.contrib import admin
from .models import APIUsageLog
 
@admin.register(APIUsageLog)
class APIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'method', 'status_code', 'timestamp')
    # search_fields = ('user__username', 'endpoint')
    search_fields = ('user', 'endpoint')
    list_filter = ('method', 'status_code')