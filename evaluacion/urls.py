from django.urls import path

from . import views

urlpatterns = [
    path('formulario/', views.FormularioView.as_view(), name='formulario'),
    path('gracias/', views.GraciasView.as_view(), name='gracias'),
    path('resultados/<str:clave>/', views.DashboardView.as_view(), name='dashboard'),
    path('api/evaluacion/', views.EvaluacionCreateView.as_view(), name='evaluacion-create'),
    path('api/resultados/<str:clave>/', views.ResultadosView.as_view(), name='resultados'),
]
