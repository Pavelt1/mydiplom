from rest_framework import serializers

from .models import Shop, Product, ProductInfo, Category, Contact, Order, OrderItem, User


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('name', 'url')

