from rest_framework import serializers
from .models import Cart, CartItem
import requests


class CartItemSerializer(serializers.ModelSerializer):
    # Additional fields to display product information
    title = serializers.SerializerMethodField()
    brand = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product_id', 'quantity', 'title', 'brand', 'price', 'image_url']
    
    def _get_product_info(self, product_id):
        """Fetch product info from product-service"""
        try:
            # Try multiple endpoints
            urls = [
                f"http://product-service:8000/api/products/{product_id}/",
                f"http://localhost:8003/api/products/{product_id}/",
                f"http://localhost:8000/api/products/{product_id}/",
            ]
            for url in urls:
                try:
                    resp = requests.get(url, timeout=2)
                    if resp.status_code == 200:
                        return resp.json()
                except:
                    continue
        except Exception:
            pass
        return {}
    
    def get_title(self, obj):
        product = self._get_product_info(obj.product_id)
        return product.get('title', 'Unknown Product')
    
    def get_brand(self, obj):
        product = self._get_product_info(obj.product_id)
        return product.get('brand', '')
    
    def get_price(self, obj):
        product = self._get_product_info(obj.product_id)
        return float(product.get('price', 0))
    
    def get_image_url(self, obj):
        product = self._get_product_info(obj.product_id)
        return product.get('image_url', '')


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'customer_id', 'items', 'total']
    
    def get_total(self, obj):
        """Calculate total price of all items in cart"""
        total = 0
        try:
            for item in obj.items.all():
                # Get product price
                try:
                    urls = [
                        f"http://product-service:8000/api/products/{item.product_id}/",
                        f"http://localhost:8003/api/products/{item.product_id}/",
                        f"http://localhost:8000/api/products/{item.product_id}/",
                    ]
                    for url in urls:
                        try:
                            resp = requests.get(url, timeout=2)
                            if resp.status_code == 200:
                                product = resp.json()
                                price = float(product.get('price', 0))
                                total += price * item.quantity
                                break
                        except:
                            continue
                except:
                    pass
        except:
            pass
        return total
