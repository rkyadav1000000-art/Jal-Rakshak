from django.contrib import admin
from .models import PollutionReport


@admin.register(PollutionReport)
class PollutionReportAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'location',
        'category',
        'created_at',
        'is_resolved',
    )

    list_filter = ('category', 'is_resolved')

    search_fields = ('title', 'location', 'description')

    list_editable = ('is_resolved',)

    ordering = ('-created_at',)


    from django.contrib import admin
from .models import PollutionReport, TapWaterTest


@admin.register(TapWaterTest)
class TapWaterTestAdmin(admin.ModelAdmin):
    list_display = (
        'village',
        'district',
        'block',
        'sample_date',
        'lab_name',
        'arsenic',
        'free_residual_chlorine',
        'total_coliform_detected',
    )

    list_filter = ('state', 'district', 'sample_date')

    search_fields = ('village', 'district', 'block')