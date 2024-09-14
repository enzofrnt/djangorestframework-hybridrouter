from rest_framework.viewsets import ModelViewSet  
from rest_framework.serializers import ModelSerializer
from .models import Auto  

class AutoSerializer(ModelSerializer):
    class Meta:
        model = Auto
        fields = '__all__'

class AutoModelViewSet(ModelViewSet):
    model = Auto
    queryset = Auto.objects.all()
    serializer_class = AutoSerializer