from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Actividad, Pregunta, RespuestaAbierta, RespuestaEscala
from .serializers import EvaluacionCreateSerializer


class EvaluacionCreateView(APIView):
    def post(self, request):
        serializer = EvaluacionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            evaluacion = serializer.save(ip_origen=request.META.get('REMOTE_ADDR'))
        except ValidationError as exc:
            return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {'error': 'Ocurrió un error inesperado al guardar la evaluación.'},
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

        preguntas_escala = []
        for pregunta in Pregunta.objects.filter(tipo=Pregunta.TIPO_ESCALA).order_by('orden'):
            respuestas = RespuestaEscala.objects.filter(
                evaluacion__actividad=actividad,
                pregunta=pregunta,
            )
            conteos = {
                opcion: respuestas.filter(valor=opcion).count()
                for opcion in ['MB', 'B', 'R', 'D', 'MD', 'NA']
            }
            valores = [
                RespuestaEscala.VALOR_NUMERICO[valor]
                for valor in respuestas.exclude(valor='NA').values_list('valor', flat=True)
                if valor in RespuestaEscala.VALOR_NUMERICO
            ]
            promedio = round(sum(valores) / len(valores), 1) if valores else None

            preguntas_escala.append(
                {
                    'codigo': pregunta.codigo,
                    'texto': pregunta.texto,
                    'seccion': pregunta.seccion,
                    'promedio': promedio,
                    'total_respuestas': respuestas.count(),
                    'conteos': conteos,
                }
            )

        respuestas_abiertas = []
        for pregunta in Pregunta.objects.filter(tipo=Pregunta.TIPO_ABIERTA).order_by('orden'):
            textos = list(
                RespuestaAbierta.objects.filter(
                    evaluacion__actividad=actividad,
                    pregunta=pregunta,
                )
                .exclude(texto='')
                .order_by('-evaluacion__enviada_en')
                .values_list('texto', flat=True)
            )
            respuestas_abiertas.append(
                {
                    'codigo': pregunta.codigo,
                    'texto_pregunta': pregunta.texto,
                    'respuestas': textos,
                }
            )

        return Response(
            {
                'actividad': {
                    'nombre': actividad.nombre,
                    'tipo_actividad': actividad.tipo_actividad,
                    'expositor': actividad.expositor,
                    'fecha': actividad.fecha.isoformat(),
                },
                'total_evaluaciones': actividad.evaluaciones.count(),
                'preguntas_escala': preguntas_escala,
                'respuestas_abiertas': respuestas_abiertas,
            }
        )
