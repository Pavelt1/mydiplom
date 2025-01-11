from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response

from backend_app.permissions import IsInGroup, IsOwnerOrReadOnly
from rest_framework.permissions import IsAuthenticated 
from .serializers import ShopSerializer
from .models import Shop
from drf_spectacular.utils import extend_schema


class Index(APIView):
    # permission_classes = (IsAuthenticated,) 

    def get(self, request):
        content = {'message': 'Hello, User!'}
        return Response(content)
    
class Shop(ModelViewSet):
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer
    required_groups = ['shop','Магазин']
    
    def get_permissions(self):
        if self.action == 'create':
            permission_classes = [IsAuthenticated,IsInGroup]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated,IsInGroup,IsOwnerOrReadOnly]
        return [permission() for permission in permission_classes]
    