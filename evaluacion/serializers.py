from django.db import transaction
from rest_framework import serializers

from .models import Actividad, Evaluacion, Pregunta, RespuestaAbierta, RespuestaEscala


class RespuestaEscalaInputSerializer(serializers.Serializer):
    pregunta_codigo = serializers.CharField()
    valor = serializers.ChoiceField(choices=['NA', 'MB', 'B', 'R', 'D', 'MD'])


class RespuestaAbiertaInputSerializer(serializers.Serializer):
    pregunta_codigo = serializers.CharField()
    texto = serializers.CharField(allow_blank=True, required=False)


class EvaluacionCreateSerializer(serializers.Serializer):
    cedula = serializers.CharField(max_length=30)
    nombre = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=150)
    respuestas_escala = RespuestaEscalaInputSerializer(many=True)
    respuestas_abiertas = RespuestaAbiertaInputSerializer(many=True, required=False)

    def validate_cedula(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('La cédula es requerida.')
        if len(value) < 5 or len(value) > 30:
            raise serializers.ValidationError('La cédula debe tener entre 5 y 30 caracteres.')
        return value

    def validate_respuestas_escala(self, value):
        if len(value) < 10:
            raise serializers.ValidationError('Debe enviar al menos 10 respuestas de escala.')
        return value

    def validate(self, attrs):
        respuestas_escala = attrs.get('respuestas_escala', [])
        respuestas_abiertas = attrs.get('respuestas_abiertas', [])

        codigos_escala = [respuesta['pregunta_codigo'] for respuesta in respuestas_escala]
        codigos_abiertas = [respuesta['pregunta_codigo'] for respuesta in respuestas_abiertas]
        codigos = set(codigos_escala + codigos_abiertas)
        preguntas = Pregunta.objects.in_bulk(codigos, field_name='codigo')

        for codigo in codigos_escala:
            pregunta = preguntas.get(codigo)
            if pregunta is None:
                raise serializers.ValidationError(
                    f'La pregunta de escala con código {codigo} no existe.'
                )
            if pregunta.tipo != Pregunta.TIPO_ESCALA:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no es de tipo escala.'
                )

        for codigo in codigos_abiertas:
            pregunta = preguntas.get(codigo)
            if pregunta is None:
                raise serializers.ValidationError(
                    f'La pregunta abierta con código {codigo} no existe.'
                )
            if pregunta.tipo != Pregunta.TIPO_ABIERTA:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no es de tipo abierta.'
                )

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        respuestas_escala = validated_data.pop('respuestas_escala')
        respuestas_abiertas = validated_data.pop('respuestas_abiertas', [])
        ip_origen = validated_data.pop('ip_origen', None)

        actividad = Actividad.objects.filter(activa=True).first()
        if actividad is None:
            raise serializers.ValidationError('No hay ninguna actividad activa en este momento.')

        evaluacion = Evaluacion.objects.create(
            actividad=actividad,
            ip_origen=ip_origen,
            **validated_data,
        )

        codigos = {
            respuesta['pregunta_codigo']
            for respuesta in respuestas_escala + respuestas_abiertas
        }
        preguntas = Pregunta.objects.in_bulk(codigos, field_name='codigo')

        RespuestaEscala.objects.bulk_create(
            [
                RespuestaEscala(
                    evaluacion=evaluacion,
                    pregunta=preguntas[respuesta['pregunta_codigo']],
                    valor=respuesta['valor'],
                )
                for respuesta in respuestas_escala
            ]
        )

        respuestas_abiertas_a_crear = [
            RespuestaAbierta(
                evaluacion=evaluacion,
                pregunta=preguntas[respuesta['pregunta_codigo']],
                texto=respuesta.get('texto', '').strip(),
            )
            for respuesta in respuestas_abiertas
            if respuesta.get('texto', '').strip()
        ]
        RespuestaAbierta.objects.bulk_create(respuestas_abiertas_a_crear)

        return evaluacion
