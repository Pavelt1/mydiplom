from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from requests import get
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader

from .models import Shop, Category, Product, User, Contact, Order, OrderItem
from .serializers import (
    ProductSerializer, 
    ContactSerializer,
    OrderSerializer,
    OrderItemSerializer,
    UserSerializer
)
from .permissions import IsShopUser, IsOrderOwner

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

class PartnerUpdate(APIView):
    """Импорт товаров из YAML для магазинов"""
    permission_classes = [permissions.IsAuthenticated, IsShopUser]

    def post(self, request, *args, **kwargs):
        url = request.data.get('url')
        if not url:
            return JsonResponse({'Status': False, 'Error': 'Не указан URL'}, status=400)

        validate_url = URLValidator()
        try:
            validate_url(url)
        except ValidationError as e:
            return JsonResponse({'Status': False, 'Error': str(e)}, status=400)
        
        try:
            stream = get(url).content
            data = load_yaml(stream, Loader=Loader)

            with transaction.atomic():
                shop, created = Shop.objects.update_or_create(
                    name=data['shop'],
                    defaults={'user': request.user, 'url': url}
                )

                for category_data in data['categories']:
                    category, _ = Category.objects.get_or_create(
                        id=category_data['id'],
                        defaults={'name': category_data['name']}
                    )
                    category.shops.add(shop)
                    category.save()

                Product.objects.filter(user=request.user).delete()

                for item in data['goods']:
                    product = Product.objects.create(
                        name=item['name'],
                        ID_product=item['id'],
                        price=item['price'],
                        quantity=item['quantity'],
                        info=str(item.get('parameters', '')),  
                        category_id=item['category'],
                        user=request.user,
                        model=item.get('model', ''),
                        price_rrc=item.get('price_rrc')
                    )

                return JsonResponse({'Status': True})

        except Exception as e:
            return JsonResponse({'Status': False, 'Error': str(e)}, status=500)

class CustomAuthToken(ObtainAuthToken):
    """Авторизация с возвратом токена и данных пользователя"""
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'email': user.email,
            'type': user.type
        })

class UserRegistration(generics.CreateAPIView):
    """Регистрация пользователей"""
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

class ProductListView(generics.ListAPIView):
    """Список товаров с фильтрацией"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filterset_fields = ['category', 'user__shop__name']
    permission_classes = [permissions.AllowAny]

class ProductDetailView(generics.RetrieveAPIView):
    """Детальная информация о товаре"""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]

class CartView(generics.GenericAPIView):
    """Управление корзиной"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Просмотр корзины"""
        order = self._get_or_create_cart()
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
    def post(self, request):
        """Добавление товара в корзину"""
        order = self._get_or_create_cart()
        serializer = OrderItemSerializer(data=request.data)
        
        if serializer.is_valid():
            product = serializer.validated_data['product']
            quantity = serializer.validated_data['quantity']
            
            available = product.quantity - product.reserved
            if available < quantity:
                return Response(
                    {'error': f'Доступно только {available} единиц товара'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            with transaction.atomic():
                product.reserved += quantity
                product.save()
                
                OrderItem.objects.update_or_create(
                    order=order,
                    product=product,
                    defaults={'quantity': quantity}
                )
            
            return Response({'status': 'Товар добавлен в корзину'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, product_id):
        """Удаление товара из корзины"""
        order = self._get_or_create_cart()
        try:
            item = OrderItem.objects.get(order=order, product_id=product_id)
            with transaction.atomic():
                product = item.product
                product.reserved -= item.quantity
                product.save()
                item.delete()
            return Response({'status': 'Товар удален из корзины'})
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Товар не найден в корзине'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def _get_or_create_cart(self):
        return Order.objects.get_or_create(
            user=self.request.user,
            state='basket'
        )[0]

class ContactView(generics.ListCreateAPIView):
    """Управление контактами доставки"""
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class OrderConfirmView(generics.GenericAPIView):
    """Подтверждение заказа"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        order = Order.objects.filter(
            user=request.user, 
            state='basket'
        ).first()
        
        if not order:
            return Response(
                {'error': 'Нет активной корзины'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not order.contact:
            return Response(
                {'error': 'Необходимо указать контактные данные'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                for item in order.ordered_items.all():
                    product = item.product
                    if product.quantity < item.quantity:
                        raise ValidationError(
                            f'Недостаточно товара: {product.name}'
                        )
                    product.quantity -= item.quantity
                    product.reserved -= item.quantity
                    product.save()
                
                order.state = 'new'
                order.save()
                self._send_confirmation_email(order)
                
            return Response({'status': 'Заказ подтвержден'})
        
        except ValidationError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def _send_confirmation_email(self, order):
        subject = f'Подтверждение заказа №{order.id}'
        message = f'Ваш заказ №{order.id} успешно оформлен.\n\nСостав заказа:\n'
        message += '\n'.join(
            [f'{item.product.name} - {item.quantity} шт.' 
             for item in order.ordered_items.all()]
        )
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )

class OrderListView(generics.ListAPIView):
    """Список заказов пользователя"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).exclude(state='basket').prefetch_related('ordered_items')

class OrderDetailView(generics.RetrieveAPIView):
    """Детали заказа"""
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrderOwner]

    def get_queryset(self):
        return Order.objects.exclude(state='basket')

class OrderStatusView(generics.UpdateAPIView):
    """Обновление статуса заказа (для магазинов)"""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsShopUser]
    http_method_names = ['patch']

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_state = request.data.get('state')
        
        if new_state not in dict(STATE_CHOICES).keys():
            return Response(
                {'error': 'Недопустимый статус'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shop_products = Product.objects.filter(user=request.user)
        order_items = instance.ordered_items.filter(product__in=shop_products)
        
        if not order_items.exists():
            return Response(
                {'error': 'В заказе нет товаров вашего магазина'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        instance.state = new_state
        instance.save()
        return Response({'status': 'Статус заказа обновлен'})