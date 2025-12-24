from django.db import models

class DiscountItem(models.Model):
    name = models.CharField(max_length=100)
    text = models.CharField(max_length=100)
    image = models.ImageField(upload_to='discount_images/')
    is_available = models.BooleanField(default=True)

    discount_type = models.CharField(
        max_length=10,
        choices=[
            ('PERCENT', 'Процент'),
            ('GIFT_ITEM', 'Товар в подарок'),
        ],
        default='PERCENT'
    )

    discount_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    min_item_qty = models.IntegerField(null=True, blank=True)
    is_first_order_only = models.BooleanField(default=False)
    every_n_item_free = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name