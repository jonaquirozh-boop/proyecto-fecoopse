import json

from django.http import Http404
from django.template.defaultfilters import slugify
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Actividad, Pregunta,
    RespuestaAbierta, RespuestaEscala, RespuestaCondicional,
)
from .serializers import EvaluacionCreateSerializer


class FormularioView(TemplateView):
    template_name = 'evaluacion/formulario.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        import json
        actividad = Actividad.objects.filter(activa=True).first()
        ctx['actividad'] = actividad

        preguntas_escala = list(
            Pregunta.objects.filter(tipo='escala').order_by('orden').values(
                'codigo', 'texto', 'seccion', 'pantalla', 'orden'
            )
        )
        preguntas_condicionales = list(
            Pregunta.objects.filter(tipo='condicional').order_by('orden').values(
                'codigo', 'texto', 'seccion', 'pantalla', 'orden'
            )
        )
        preguntas_abiertas = list(
            Pregunta.objects.filter(tipo='abierta').order_by('orden').values(
                'codigo', 'texto', 'seccion', 'pantalla', 'orden'
            )
        )

        ctx['preguntas_escala_json'] = json.dumps(preguntas_escala)
        ctx['preguntas_condicionales_json'] = json.dumps(preguntas_condicionales)
        ctx['preguntas_abiertas_json'] = json.dumps(preguntas_abiertas)
        return ctx


class GraciasView(TemplateView):
    template_name = 'evaluacion/gracias.html'


class DashboardView(TemplateView):
    template_name = 'evaluacion/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        clave = self.kwargs.get('clave')

        try:
            actividad = Actividad.objects.get(clave_resultados=clave)
        except Actividad.DoesNotExist:
            raise Http404

        import json

        # Preguntas de escala con conteos y promedios
        preguntas_escala = []
        for pregunta in Pregunta.objects.filter(tipo='escala').order_by('orden'):
            respuestas = RespuestaEscala.objects.filter(
                evaluacion__actividad=actividad,
                pregunta=pregunta,
            )
            conteos = {
                '5': respuestas.filter(valor=5).count(),
                '4': respuestas.filter(valor=4).count(),
                '3': respuestas.filter(valor=3).count(),
                '2': respuestas.filter(valor=2).count(),
                '1': respuestas.filter(valor=1).count(),
                'NA': respuestas.filter(valor__isnull=True).count(),
            }
            valores = list(
                respuestas.exclude(valor__isnull=True).values_list('valor', flat=True)
            )
            promedio = round(sum(valores)/len(valores), 1) if valores else None
            preguntas_escala.append({
                'codigo': pregunta.codigo,
                'texto': pregunta.texto,
                'seccion': pregunta.seccion,
                'pantalla': pregunta.pantalla,
                'promedio': promedio,
                'total_respuestas': respuestas.count(),
                'total_validas': len(valores),
                'conteos': conteos,
            })

        # Preguntas condicionales
        preguntas_condicionales = []
        for pregunta in Pregunta.objects.filter(tipo='condicional').order_by('orden'):
            respuestas = RespuestaCondicional.objects.filter(
                evaluacion__actividad=actividad,
                pregunta=pregunta,
            )
            conteos = {
                'SI': respuestas.filter(opcion='SI').count(),
                'PARCIAL': respuestas.filter(opcion='PARCIAL').count(),
                'NO': respuestas.filter(opcion='NO').count(),
            }
            justificaciones = list(
                respuestas.exclude(justificacion='')
                .order_by('-evaluacion__enviada_en')
                .values('opcion', 'justificacion')
            )
            preguntas_condicionales.append({
                'codigo': pregunta.codigo,
                'texto': pregunta.texto,
                'conteos': conteos,
                'justificaciones': justificaciones,
            })

        # Preguntas abiertas
        respuestas_abiertas = []
        for pregunta in Pregunta.objects.filter(tipo='abierta').order_by('orden'):
            textos = list(
                RespuestaAbierta.objects.filter(
                    evaluacion__actividad=actividad,
                    pregunta=pregunta,
                ).exclude(texto='').order_by('-evaluacion__enviada_en')
                .values_list('texto', flat=True)
            )
            respuestas_abiertas.append({
                'codigo': pregunta.codigo,
                'texto_pregunta': pregunta.texto,
                'respuestas': textos,
            })

        # Agrupar escala por sección para el template
        secciones = {}
        for p in preguntas_escala:
            sec = p['seccion']
            if sec not in secciones:
                secciones[sec] = []
            secciones[sec].append(p)

        # Promedio general (excluyendo NA)
        todos = [p['promedio'] for p in preguntas_escala if p['promedio'] is not None]
        promedio_general = round(sum(todos)/len(todos), 1) if todos else None

        ctx['actividad'] = actividad
        ctx['total_evaluaciones'] = actividad.evaluaciones.count()
        ctx['promedio_general'] = promedio_general
        ctx['secciones'] = secciones
        ctx['preguntas_escala'] = preguntas_escala
        ctx['preguntas_condicionales'] = preguntas_condicionales
        ctx['respuestas_abiertas'] = respuestas_abiertas
        ctx['preguntas_escala_json'] = json.dumps(preguntas_escala)
        ctx['preguntas_condicionales_json'] = json.dumps(preguntas_condicionales)
        return ctx


class EvaluacionCreateView(APIView):
    def post(self, request):
        serializer = EvaluacionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            evaluacion = serializer.save(ip_origen=request.META.get('REMOTE_ADDR'))
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response(
                {'error': 'Ocurrió un error al guardar la evaluación.', 'detalle': str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                'mensaje': 'Evaluación enviada correctamente.',
                'id': evaluacion.id,
            },
            status=status.HTTP_201_CREATED,
        )


class ResultadosView(APIView):
    def get(self, request, clave):
        try:
            actividad = Actividad.objects.get(clave_resultados=clave)
        except Actividad.DoesNotExist:
            return Response({'error': 'No encontrado'}, status=status.HTTP_404_NOT_FOUND)

        # Preguntas de ESCALA: agrupadas por pantalla
        preguntas_escala = []
        for pregunta in Pregunta.objects.filter(tipo=Pregunta.TIPO_ESCALA).order_by('orden'):
            respuestas = RespuestaEscala.objects.filter(
                evaluacion__actividad=actividad,
                pregunta=pregunta,
            )
            # Conteos por valor (1-5) y NA (NULL)
            conteos = {
                '5': respuestas.filter(valor=5).count(),
                '4': respuestas.filter(valor=4).count(),
                '3': respuestas.filter(valor=3).count(),
                '2': respuestas.filter(valor=2).count(),
                '1': respuestas.filter(valor=1).count(),
                'NA': respuestas.filter(valor__isnull=True).count(),
            }
            # Promedio excluyendo NA (NULL)
            valores_numericos = list(
                respuestas.exclude(valor__isnull=True).values_list('valor', flat=True)
            )
            promedio = (
                round(sum(valores_numericos) / len(valores_numericos), 1)
                if valores_numericos else None
            )

            preguntas_escala.append({
                'codigo': pregunta.codigo,
                'texto': pregunta.texto,
                'seccion': pregunta.seccion,
                'pantalla': pregunta.pantalla,
                'promedio': promedio,
                'total_respuestas': respuestas.count(),
                'total_validas': len(valores_numericos),  # excluyendo NA
                'conteos': conteos,
            })

        # Preguntas CONDICIONALES
        preguntas_condicionales = []
        for pregunta in Pregunta.objects.filter(tipo=Pregunta.TIPO_CONDICIONAL).order_by('orden'):
            respuestas = RespuestaCondicional.objects.filter(
                evaluacion__actividad=actividad,
                pregunta=pregunta,
            )
            conteos = {
                'SI': respuestas.filter(opcion='SI').count(),
                'PARCIAL': respuestas.filter(opcion='PARCIAL').count(),
                'NO': respuestas.filter(opcion='NO').count(),
            }
            justificaciones = list(
                respuestas.exclude(justificacion='')
                .order_by('-evaluacion__enviada_en')
                .values_list('opcion', 'justificacion')
            )
            preguntas_condicionales.append({
                'codigo': pregunta.codigo,
                'texto': pregunta.texto,
                'seccion': pregunta.seccion,
                'pantalla': pregunta.pantalla,
                'total_respuestas': respuestas.count(),
                'conteos': conteos,
                'justificaciones': [
                    {'opcion': op, 'texto': txt} for op, txt in justificaciones
                ],
            })

        # Preguntas ABIERTAS
        preguntas_abiertas = []
        for pregunta in Pregunta.objects.filter(tipo=Pregunta.TIPO_ABIERTA).order_by('orden'):
            textos = list(
                RespuestaAbierta.objects.filter(
                    evaluacion__actividad=actividad,
                    pregunta=pregunta,
                ).exclude(texto='').order_by('-evaluacion__enviada_en')
                .values_list('texto', flat=True)
            )
            preguntas_abiertas.append({
                'codigo': pregunta.codigo,
                'texto_pregunta': pregunta.texto,
                'pantalla': pregunta.pantalla,
                'respuestas': textos,
            })

        return Response({
            'actividad': {
                'nombre': actividad.nombre,
                'tipo_actividad': actividad.tipo_actividad,
                'expositor': actividad.expositor,
                'fecha': actividad.fecha.isoformat(),
            },
            'total_evaluaciones': actividad.evaluaciones.count(),
            'preguntas_escala': preguntas_escala,
            'preguntas_condicionales': preguntas_condicionales,
            'preguntas_abiertas': preguntas_abiertas,
        })
