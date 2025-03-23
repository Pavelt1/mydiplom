from django.db import models

STATE_CHOICES = (
    ('basket', 'Статус корзины'),
    ('new', 'Новый'),
    ('confirmed', 'Подтвержден'),
    ('assembled', 'Собран'),
    ('sent', 'Отправлен'),
    ('delivered', 'Доставлен'),
    ('canceled', 'Отменен'),
)

USER_TYPE_CHOICES = (
    ('shop', 'Магазин'),
    ('buyer', 'Покупатель'),
)

class User(models.Model):
    username = models.CharField(max_length=50, verbose_name='Логин')
    password = models.CharField(max_length=50, verbose_name='Пароль')
    first_name = models.CharField(max_length=50,blank=True, null=True,verbose_name='Имя')
    last_name = models.CharField(max_length=50,blank=True, null=True,verbose_name='Фамилия')
    age = models.IntegerField(blank=True, null=True,verbose_name='Возраст')
    email = models.EmailField(unique=True, verbose_name='Почта')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    type = models.CharField(verbose_name='Тип пользователя', choices=USER_TYPE_CHOICES, max_length=5, default='buyer')


    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['created_at','type']

    def __str__(self):
        if self.first_name:
            if self.last_name:
                return f'{self.first_name} {self.last_name}'
            return self.first_name
        return self.username



class Shop(models.Model):
    name = models.CharField(max_length=50,verbose_name='Название магазина',unique=True)
    url = models.URLField(blank=True,null=True,verbose_name='Ссылка')
    user = models.OneToOneField(User, verbose_name='Пользователь',
                                blank=True, null=True,
                                on_delete=models.CASCADE)#Обдумать несколько владельцев магазина

    class Meta:
        verbose_name = 'Mагазин'
        verbose_name_plural = 'Mагазины'
        ordering = ['name']

    def __str__(self):
        return self.name
        
class Category(models.Model):
    name = models.CharField(max_length=50,verbose_name='Название категории')
    shops = models.ManyToManyField(Shop,verbose_name='Магазины',related_name='categories')

    class Meta:
        verbose_name = 'Категория'        
        verbose_name_plural = 'Категории'
        ordering = ['name']


    def __str__(self):
        return self.name
        
class Product(models.Model):
    name = models.CharField(max_length=50,verbose_name='Название товара')
    ID_product = models.PositiveIntegerField(verbose_name='ID продукта')
    info = models.CharField(max_length=1000,verbose_name='Информация',blank=True,null=True)
    quantity = models.PositiveIntegerField(verbose_name='Количество')
    price = models.PositiveIntegerField(verbose_name='Цена')
    price_rrc = models.PositiveIntegerField(null=True, blank=True)
    model = models.CharField(max_length=100, blank=True)

    category = models.ForeignKey(Category,verbose_name='Категория',related_name='products',on_delete=models.CASCADE)
    user = models.ForeignKey(User,verbose_name='Пользователь',related_name='products',on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Продукт'        
        verbose_name_plural = 'Список всех товаров'
        ordering = ['ID_product']

    def __str__(self):
        return self.name
        

class Contact(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='contacts', blank=True,
                             on_delete=models.CASCADE)

    city = models.CharField(max_length=50, verbose_name='Город')
    street = models.CharField(max_length=100, verbose_name='Улица')
    house = models.CharField(max_length=15, verbose_name='Дом', blank=True)
    structure = models.CharField(max_length=15, verbose_name='Корпус', blank=True)
    building = models.CharField(max_length=15, verbose_name='Строение', blank=True)
    apartment = models.CharField(max_length=15, verbose_name='Квартира', blank=True)
    phone = models.CharField(max_length=20, verbose_name='Телефон')

    class Meta:
        verbose_name = 'Контант'        
        verbose_name_plural = 'Контакты'
        ordering = ['user']

    def __str__(self):
        return f'{self.city} {self.street} {self.house}'


class Order(models.Model):
    user = models.ForeignKey(User, verbose_name='Пользователь',
                             related_name='orders', blank=True,
                             on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    state = models.CharField(verbose_name='Статус', choices=STATE_CHOICES, max_length=15,default='new')
    contact = models.ForeignKey(Contact, verbose_name='Контакт',
                                blank=True, null=True,
                                on_delete=models.CASCADE)
    
    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = "Список заказ"
        ordering = ('-date',)

    def __str__(self):
        return str(self.date)
    
class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name='Заказ', related_name='ordered_items', blank=True,
                              on_delete=models.CASCADE)

    product = models.ForeignKey(Product, verbose_name='продукт', related_name='ordered_items',
                                     blank=True,
                                     on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='Количество')

    class Meta:
        verbose_name = 'Заказанная позиция'
        verbose_name_plural = "Список заказанных позиций"