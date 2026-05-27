from django.db import transaction
from rest_framework import serializers

from .models import (
    Actividad, Evaluacion, Pregunta,
    RespuestaAbierta, RespuestaEscala, RespuestaCondicional,
)


class RespuestaEscalaInputSerializer(serializers.Serializer):
    pregunta_codigo = serializers.CharField()
    # valor: integer 1-5, o null para NA
    valor = serializers.IntegerField(allow_null=True, min_value=1, max_value=5)


class RespuestaAbiertaInputSerializer(serializers.Serializer):
    pregunta_codigo = serializers.CharField()
    texto = serializers.CharField(allow_blank=True, required=False)


class RespuestaCondicionalInputSerializer(serializers.Serializer):
    pregunta_codigo = serializers.CharField()
    opcion = serializers.ChoiceField(choices=['SI', 'PARCIAL', 'NO'])
    justificacion = serializers.CharField(allow_blank=True, required=False)


class EvaluacionCreateSerializer(serializers.Serializer):
    correo = serializers.EmailField()
    respuestas_escala = RespuestaEscalaInputSerializer(many=True)
    respuestas_condicionales = RespuestaCondicionalInputSerializer(many=True, required=False)
    respuestas_abiertas = RespuestaAbiertaInputSerializer(many=True, required=False)

    def validate_correo(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError('El correo es requerido.')
        return value

    def validate_respuestas_escala(self, value):
        if len(value) < 10:
            raise serializers.ValidationError(
                'Debe responder al menos 10 preguntas de escala.'
            )
        return value

    def validate(self, attrs):
        # Verificar actividad activa
        actividad = Actividad.objects.filter(activa=True).first()
        if not actividad:
            raise serializers.ValidationError(
                'No hay ninguna actividad activa en este momento.'
            )

        # Verificar duplicado: correo + actividad ya existe?
        correo = attrs.get('correo')
        if Evaluacion.objects.filter(actividad=actividad, correo=correo).exists():
            raise serializers.ValidationError({
                'correo': 'Este correo ya completó la evaluación para esta actividad.'
            })

        # Validar códigos de preguntas
        respuestas_escala = attrs.get('respuestas_escala', [])
        respuestas_condicionales = attrs.get('respuestas_condicionales', [])
        respuestas_abiertas = attrs.get('respuestas_abiertas', [])

        codigos_escala = [r['pregunta_codigo'] for r in respuestas_escala]
        codigos_condicional = [r['pregunta_codigo'] for r in respuestas_condicionales]
        codigos_abiertas = [r['pregunta_codigo'] for r in respuestas_abiertas]
        todos_codigos = set(codigos_escala + codigos_condicional + codigos_abiertas)

        preguntas = Pregunta.objects.in_bulk(todos_codigos, field_name='codigo')

        for codigo in codigos_escala:
            p = preguntas.get(codigo)
            if not p:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no existe.'
                )
            if p.tipo != Pregunta.TIPO_ESCALA:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no es de tipo escala.'
                )

        for codigo in codigos_condicional:
            p = preguntas.get(codigo)
            if not p:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no existe.'
                )
            if p.tipo != Pregunta.TIPO_CONDICIONAL:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no es de tipo condicional.'
                )

        for codigo in codigos_abiertas:
            p = preguntas.get(codigo)
            if not p:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no existe.'
                )
            if p.tipo != Pregunta.TIPO_ABIERTA:
                raise serializers.ValidationError(
                    f'La pregunta {codigo} no es de tipo abierta.'
                )

        # Guardar actividad en attrs para usarla en create()
        attrs['_actividad'] = actividad
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        respuestas_escala = validated_data.pop('respuestas_escala')
        respuestas_condicionales = validated_data.pop('respuestas_condicionales', [])
        respuestas_abiertas = validated_data.pop('respuestas_abiertas', [])
        actividad = validated_data.pop('_actividad')
        ip_origen = validated_data.pop('ip_origen', None)

        evaluacion = Evaluacion.objects.create(
            actividad=actividad,
            correo=validated_data['correo'],
            ip_origen=ip_origen,
        )

        # Recolectar todos los códigos
        todos = (
            [r['pregunta_codigo'] for r in respuestas_escala]
            + [r['pregunta_codigo'] for r in respuestas_condicionales]
            + [r['pregunta_codigo'] for r in respuestas_abiertas]
        )
        preguntas = Pregunta.objects.in_bulk(set(todos), field_name='codigo')

        # Crear respuestas de escala (valor puede ser NULL para NA)
        RespuestaEscala.objects.bulk_create([
            RespuestaEscala(
                evaluacion=evaluacion,
                pregunta=preguntas[r['pregunta_codigo']],
                valor=r['valor'],
            )
            for r in respuestas_escala
        ])

        # Crear respuestas condicionales
        RespuestaCondicional.objects.bulk_create([
            RespuestaCondicional(
                evaluacion=evaluacion,
                pregunta=preguntas[r['pregunta_codigo']],
                opcion=r['opcion'],
                justificacion=r.get('justificacion', '').strip(),
            )
            for r in respuestas_condicionales
        ])

        # Crear respuestas abiertas (solo si tienen texto)
        RespuestaAbierta.objects.bulk_create([
            RespuestaAbierta(
                evaluacion=evaluacion,
                pregunta=preguntas[r['pregunta_codigo']],
                texto=r.get('texto', '').strip(),
            )
            for r in respuestas_abiertas
            if r.get('texto', '').strip()
        ])

        return evaluacion
