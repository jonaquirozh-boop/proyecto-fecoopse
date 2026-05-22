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

    TIPOS = [
        (TIPO_ESCALA, 'Escala'),
        (TIPO_ABIERTA, 'Abierta'),
    ]

    codigo = models.CharField(max_length=10, unique=True)
    texto = models.TextField()
    seccion = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPOS)
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
    cedula = models.CharField(max_length=30)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=150)
    enviada_en = models.DateTimeField(auto_now_add=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Evaluación"
        verbose_name_plural = "Evaluaciones"
        ordering = ['-enviada_en']

    def __str__(self):
        return f"{self.nombre} {self.apellidos} - {self.actividad.nombre}"


class RespuestaEscala(models.Model):
    OPCIONES_ESCALA = [
        ('NA', 'No Aplica'),
        ('MB', 'Muy Bueno'),
        ('B', 'Bueno'),
        ('R', 'Regular'),
        ('D', 'Deficiente'),
        ('MD', 'Muy Deficiente'),
    ]

    VALOR_NUMERICO = {
        'MB': 5,
        'B': 4,
        'R': 3,
        'D': 2,
        'MD': 1,
    }

    evaluacion = models.ForeignKey(
        Evaluacion,
        on_delete=models.CASCADE,
        related_name='respuestas_escala',
    )
    pregunta = models.ForeignKey(Pregunta, on_delete=models.PROTECT)
    valor = models.CharField(max_length=2, choices=OPCIONES_ESCALA)

    class Meta:
        verbose_name = "Respuesta de escala"
        verbose_name_plural = "Respuestas de escala"
        unique_together = ['evaluacion', 'pregunta']

    def __str__(self):
        return f"{self.pregunta.codigo}: {self.get_valor_display()}"


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
