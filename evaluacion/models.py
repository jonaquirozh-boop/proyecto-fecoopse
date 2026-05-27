import secrets

from django.db import models


class Actividad(models.Model):
    nombre = models.CharField(max_length=200)
    tipo_actividad = models.CharField(max_length=100)
    expositor = models.CharField(max_length=200)
    fecha = models.DateField()
    clave_resultados = models.CharField(max_length=64, unique=True, blank=True)
    activa = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Actividad"
        verbose_name_plural = "Actividades"
        ordering = ['-creado_en']

    def save(self, *args, **kwargs):
        if not self.clave_resultados:
            self.clave_resultados = secrets.token_urlsafe(16)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} ({self.fecha})"


class Pregunta(models.Model):
    TIPO_ESCALA = 'escala'
    TIPO_ABIERTA = 'abierta'
    TIPO_CONDICIONAL = 'condicional'

    TIPOS = [
        (TIPO_ESCALA, 'Escala'),
        (TIPO_ABIERTA, 'Abierta'),
        (TIPO_CONDICIONAL, 'Condicional'),
    ]

    codigo = models.CharField(max_length=10, unique=True)
    texto = models.TextField()
    seccion = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
    pantalla = models.CharField(max_length=50, blank=True)
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Pregunta"
        verbose_name_plural = "Preguntas"
        ordering = ['orden']

    def __str__(self):
        return f"{self.codigo} - {self.texto[:60]}"


class Evaluacion(models.Model):
    actividad = models.ForeignKey(
        Actividad,
        on_delete=models.CASCADE,
        related_name='evaluaciones',
    )
    correo = models.EmailField()
    enviada_en = models.DateTimeField(auto_now_add=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ['-enviada_en']
        unique_together = ['actividad', 'correo']

    def __str__(self):
        return f"{self.correo} - {self.actividad.nombre}"


class RespuestaEscala(models.Model):
    OPCIONES_ESCALA = [
        (5, 'MB - Muy Bueno'),
        (4, 'B - Bueno'),
        (3, 'R - Regular'),
        (2, 'D - Deficiente'),
        (1, 'MD - Muy Deficiente'),
    ]

    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='respuestas_escala',
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    valor = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Respuesta de escala"
        verbose_name_plural = "Respuestas de escala"
        unique_together = ['evaluacion', 'pregunta']

    def __str__(self):
        if self.valor is None:
            return f"{self.pregunta.codigo}: NA"
        return f"{self.pregunta.codigo}: {self.valor}"


class RespuestaCondicional(models.Model):
    OPCIONES = [
        ('SI', 'Sí'),
        ('PARCIAL', 'Parcialmente'),
        ('NO', 'No'),
    ]

    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='respuestas_condicionales',
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    opcion = models.CharField(max_length=10, choices=OPCIONES)
    justificacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Respuesta condicional"
        verbose_name_plural = "Respuestas condicionales"
        unique_together = ['evaluacion', 'pregunta']

    def __str__(self):
        return f"{self.pregunta.codigo}: {self.get_opcion_display()}"


class RespuestaAbierta(models.Model):
    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='respuestas_abiertas',
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    texto = models.TextField(blank=True)

    class Meta:
        verbose_name = "Respuesta abierta"
        verbose_name_plural = "Respuestas abiertas"
        unique_together = ['evaluacion', 'pregunta']

    def __str__(self):
        return f"{self.pregunta.codigo}: {self.texto[:50]}"
