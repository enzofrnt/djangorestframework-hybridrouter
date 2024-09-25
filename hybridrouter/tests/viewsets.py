from rest_framework.viewsets import ModelViewSet
from .models import Item
from .serializers import ItemSerializer


class ItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class SlugItemViewSet(ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    lookup_field = "name"
