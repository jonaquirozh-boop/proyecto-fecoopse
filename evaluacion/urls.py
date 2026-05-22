from django.urls import path

from . import views

urlpatterns = [
    path('api/evaluacion/', views.EvaluacionCreateView.as_view(), name='evaluacion-create'),
    path('api/resultados/<str:clave>/', views.ResultadosView.as_view(), name='resultados'),
]
