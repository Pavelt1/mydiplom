from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Shop, Category, Product, Contact, Order, OrderItem

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'email', 'first_name', 
                 'last_name', 'age', 'type', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
            'created_at': {'read_only': True},
        }  # Убрали 'type' из read_only

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            type=validated_data.get('type', 'buyer')
        )
        return user

class ShopSerializer(serializers.ModelSerializer):
    categories = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = Shop
        fields = ['id', 'name', 'url', 'user', 'categories']
        extra_kwargs = {
            'user': {'read_only': True}
        }

class CategorySerializer(serializers.ModelSerializer):
    shops = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = Category
        fields = ['id', 'name', 'shops']

class ProductSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    shop = ShopSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'ID_product', 'name', 'info', 'quantity',
                 'price', 'category', 'category_id', 'shop', 'user']
        extra_kwargs = {
            'user': {'read_only': True},
            'ID_product': {'read_only': True}
        }

    def validate_quantity(self, value):
        if value < 0:
            raise serializers.ValidationError("Quantity cannot be negative")
        return value

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ['id', 'city', 'street', 'house', 'structure',
                 'building', 'apartment', 'phone']
        extra_kwargs = {
            'user': {'read_only': True}
        }

    def create(self, validated_data):
        contact = Contact.objects.create(
            user=self.context['request'].user,
            **validated_data
        )
        return contact

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_id', 'quantity']
        extra_kwargs = {
            'quantity': {'min_value': 1}
        }

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, source='ordered_items')
    total = serializers.SerializerMethodField()
    contact = ContactSerializer(read_only=True)
    contact_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = ['id', 'state', 'date', 'items', 'total', 'contact', 'contact_id']
        read_only_fields = ['date', 'total']

    def get_total(self, obj):
        return sum(item.product.price * item.quantity for item in obj.ordered_items.all())

    def validate(self, data):
        if self.context['request'].method == 'POST' and not data.get('contact_id'):
            raise serializers.ValidationError("Contact is required for order creation")
        return data

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['state']
        extra_kwargs = {
            'state': {'required': True}
        }
     