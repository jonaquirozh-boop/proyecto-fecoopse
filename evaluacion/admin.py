from django.contrib import admin

from .models import (
    Actividad,
    Evaluacion,
    Pregunta,
    RespuestaAbierta,
    RespuestaCondicional,
    RespuestaEscala,
)


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'tipo_actividad',
        'expositor',
        'fecha',
        'activa',
        'total_evaluaciones',
        'creado_en',
    )
    list_filter = ('activa', 'fecha')
    search_fields = ('nombre', 'expositor')
    readonly_fields = ('clave_resultados', 'creado_en')
    ordering = ('-creado_en',)

    def total_evaluaciones(self, obj):
        return obj.evaluaciones.count()

    total_evaluaciones.short_description = 'Total respuestas'


@admin.register(Pregunta)
class PreguntaAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'texto_corto', 'seccion', 'tipo', 'orden')
    list_filter = ('tipo', 'seccion')
    search_fields = ('codigo', 'texto')
    ordering = ('orden',)
    list_editable = ('orden',)

    def texto_corto(self, obj):
        return obj.texto[:80] + '...' if len(obj.texto) > 80 else obj.texto

    texto_corto.short_description = 'Pregunta'


class RespuestaEscalaInline(admin.TabularInline):
    model = RespuestaEscala
    extra = 0
    readonly_fields = ('pregunta', 'valor')
    can_delete = False


class RespuestaCondicionalInline(admin.TabularInline):
    model = RespuestaCondicional
    extra = 0
    readonly_fields = ('pregunta', 'opcion', 'justificacion')
    can_delete = False


class RespuestaAbiertaInline(admin.TabularInline):
    model = RespuestaAbierta
    extra = 0
    readonly_fields = ('pregunta', 'texto')
    can_delete = False


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = ('correo', 'actividad', 'enviada_en', 'total_respuestas')
    list_filter = ('actividad', 'enviada_en')
    search_fields = ('correo',)
    readonly_fields = ('enviada_en', 'ip_origen', 'correo', 'actividad')
    date_hierarchy = 'enviada_en'
    ordering = ('-enviada_en',)
    inlines = [
        RespuestaEscalaInline,
        RespuestaCondicionalInline,
        RespuestaAbiertaInline,
    ]

    def total_respuestas(self, obj):
        return (
            obj.respuestas_escala.count()
            + obj.respuestas_condicionales.count()
            + obj.respuestas_abiertas.count()
        )

    total_respuestas.short_description = 'Respuestas dadas'


@admin.register(RespuestaEscala)
class RespuestaEscalaAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'pregunta', 'valor_mostrado')
    list_filter = ('valor', 'pregunta__seccion')
    search_fields = ('evaluacion__correo', 'pregunta__codigo')

    def valor_mostrado(self, obj):
        if obj.valor is None:
            return 'NA'
        mapa = {5: 'MB', 4: 'B', 3: 'R', 2: 'D', 1: 'MD'}
        return mapa.get(obj.valor, str(obj.valor))

    valor_mostrado.short_description = 'Valor'


@admin.register(RespuestaCondicional)
class RespuestaCondicionalAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'pregunta', 'opcion', 'justificacion_corta')
    list_filter = ('opcion', 'pregunta')

    def justificacion_corta(self, obj):
        if not obj.justificacion:
            return '-'
        return obj.justificacion[:60] + ('...' if len(obj.justificacion) > 60 else '')

    justificacion_corta.short_description = 'Justificación'


@admin.register(RespuestaAbierta)
class RespuestaAbiertaAdmin(admin.ModelAdmin):
    list_display = ('evaluacion', 'pregunta', 'texto_corto')
    list_filter = ('pregunta',)
    search_fields = ('evaluacion__correo', 'texto')

    def texto_corto(self, obj):
        return obj.texto[:60] + '...' if len(obj.texto) > 60 else obj.texto

    texto_corto.short_description = 'Respuesta'


admin.site.site_header = "FECOOPSE - Administración"
admin.site.site_title = "FECOOPSE Admin"
admin.site.index_title = "Panel de Evaluaciones"
