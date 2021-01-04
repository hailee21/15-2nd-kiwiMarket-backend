import json
from django.utils import timezone
import datetime

from django.views     import View
from django.http      import JsonResponse
from django.db.models import Prefetch, Count

from .models import (
    Product,
    ProductImage,
    MainCategory,
    ProductCategory,
    ProductComment,
)

from user.models import OrderStatus, Address, User, Wishlist
from .forms import ProductFullForm

import boto3          
import uuid   


class ProductListView(View):
    def get(self, request, address_id):
        #wishcategories = Wishcategory.objects.filter(user=request.user)
        #Products = Product.objects.filter(address=address, product_category__in=wishcategories)
        try: 
            if Product.objects.filter(address=address_id).exists():
                products = Product.objects.filter(address=address_id).prefetch_related(Prefetch('productimage_set', queryset = ProductImage.objects.all(), to_attr='productimage_list'),
                                                                                        Prefetch('wishlist_set', queryset = Wishlist.objects.all(), to_attr='wishlist_list'),
                                                                                        Prefetch('productcomment_set', queryset = ProductComment.objects.all(), to_attr='comment_list'))   
                                                                                        
                result= [{
                    "itemId"           : item.id,
                    "imgSrc"           : item.productimage_list[0].image_url.url, 
                    "title"            : item.name,
                    "townName"         : (item.address.district+' '+item.address.neighborhood),
                    "postedTime"       : item.updated_at.isoformat(),            
                    "price"            : int(item.price),
                    "wishCount"        : len(item.wishlist_list),
                    "commentCount"     : len(item.comment_list),
                    "viewed"           : item.viewed,
                    "order_status"     : item.order_status.name,
                }for item in products]

                return JsonResponse({"message" : "SUCCESS", "productList" : result}, status = 200)
            return JsonResponse({"message" : "NO_PRODUCT"}, status = 400)
        except KeyError:
            return JsonResponse({'message':'INVALID_KEYS'}, status = 404)
     
class ProductDetailView(View):
    def get(self, request, product_id):
        try:
            if Product.objects.filter(id=product_id).exists():
    
                viewed_ins = Product.objects.get(id=product_id).viewed
                Product.objects.filter(id=product_id).update(viewed=viewed_ins+1)
                products = Product.objects.filter(id=product_id).prefetch_related(
                    Prefetch('productimage_set', queryset = ProductImage.objects.all(), to_attr='productimage_list'),         
                    Prefetch('wishlist_set', queryset = Wishlist.objects.filter(product_id = product_id), to_attr='wishlist_list'), 
                    Prefetch('productcomment_set', queryset = ProductComment.objects.all(), to_attr='comment_list'))   

                result= {
                    "sellerdata"    : [{
                        "seller_profilepic": '사진 데이터가 없음',
                        "seller"           : item.uploader.nickname,
                        "seller_id"        : item.uploader.id,
                        "townName"         : (item.address.district+' '+item.address.neighborhood),
                        "towncode"         : item.address.id,
                        "mannerTemperature": 36.5,                 
                    }for item in products],
                    "productdetail" : [{
                        "imgSrcList"       : [item.productimage_list[num].image_url.url for num in range(0, len(item.productimage_list))],
                        "price"            : int(item.price),
                        "title"            : item.name,    
                        "category"         : item.product_category.name,    
                        "postedTime"       : item.updated_at.isoformat(),          
                        "description"      : item.description,        
                        "wishCount"        : len(item.wishlist_list),
                        "hits"             : item.viewed,
                        "itemId"           : item.id,
                        "order_status"     : item.order_status.name,
                        "commentCount"     : len(item.comment_list),
                    }for item in products]
                }
                return JsonResponse({"message" : "SUCCESS", "itemDetailData" : result}, status = 200)
            return JsonResponse({"message" : "NO_PRODUCT"}, status = 400)
        except KeyError:
            return JsonResponse({'message':'INVALID_KEYS'}, status = 404)

class ProductUploadView(View):
    def post(self, request, address_id):  
        form = ProductFullForm(request.POST or None, request.FILES or None)
        files = request.FILES.getlist('image')
        print(form)
        print(files)
        if form.is_valid():
            uploader_ins     = User.objects.get(id=2) #데코레이터 적용 전 임시
            name             = form.cleaned_data['name']
            description      = form.cleaned_data['description']
            price            = form.cleaned_data['price']
            access_range     = form.cleaned_data['access_range']
            order_status_ins = OrderStatus.objects.get(name="판매중")
            product_category_ins = form.cleaned_data["product_category"]
            address_ins      = Address.objects.get(id=address_id)
            product_ins      = Product.objects.create(
                name=name, 
                price=price, 
                viewed=0, 
                description=description, 
                access_range=access_range, 
                created_at=0, 
                updated_at=0, 
                order_status=order_status_ins, 
                product_category=product_category_ins, 
                address = address_ins, 
                uploader = uploader_ins)
            for f in files:
                ProductImage.objects.create(product=product_ins,image_url=f)
            return JsonResponse({"message" : "SUCCESS"}, status = 200)
        return JsonResponse({"message" : "INVALID_FORM"}, status = 404)

class SellerItemsView(View):
    def get(self, request, uploader_id):
        try:
            if Product.objects.filter(uploader_id=uploader_id).exists():
                products = Product.objects.filter(uploader_id=uploader_id).prefetch_related(Prefetch('productimage_set', queryset = ProductImage.objects.all(), to_attr='productimage_list'))   

                result= [{
                    "id"               : item.id,
                    "imgSrc"           : item.productimage_list[0].image_url,
                    "title"            : item.name,
                    "price"            : int(item.price),
                    "order_status"     : item.order_status.name,
                    }for item in products]

                return JsonResponse({"message" : "SUCCESS", "sellerItemsData" : result}, status = 200)
            return JsonResponse({"message" : "NO_SELLING_PRODUCT"}, status = 400)
        except KeyError:
            return JsonResponse({'message':'INVALID_KEYS'}, status = 400)

class CommentDetailView(View):
    def get(self, request, product_id):
        try:
            if ProductComment.objects.filter(product=product_id).exists():
                #wishcategories = Wishcategory.objects.filter(user=request.user)
                #Products = Product.objects.filter(address=address, product_category__in=wishcategories)
                comments = ProductComment.objects.filter(product=product_id)
                result= {
                    "uploaderdata"    : [{
                        "uploader_profilepic": '사진 데이터가 없음',
                        "uploader"           : item.uploader.nickname,
                        "uploader_id"        : item.uploader.id,
                        # "townName"         : (item.address.address2+' '+item.address.address3),
                        # "towncode"         : item.address.id,
                        "mannerTemperature"  : 36.5,                 
                    }for item in comments],
                    "commentdetail" : [{
                        "uploader"         : item.uploader.nickname,
                        "content"          : item.content,
                        "postedTime"       : item.created_at,  
                    }for item in comments]
                }
                return JsonResponse({"message" : "SUCCESS", "commentlist" : result}, status = 200)
            return JsonResponse({"message" : "SUCCESS","commentlist" : []}, status = 400)
        except KeyError:
            return JsonResponse({'message':'INVALID_KEYS'}, status = 404)

class CommentUploadView(View):
    def post(self, request, product_id):
        data = json.loads(request.body)

        uploader_ins = User.objects.get(id=2) #데코레이터 적용 전 임시
        product_ins = Product.objects.get(id=product_id)

        ProductComment.objects.create(uploader=uploader_ins, proudct=product_ins, content=data["content"])

        return JsonResponse({"message" : "SUCCESS"}, status = 200)

class RelatedProductView(View):
    def get(self, request, address_id):
        #wishcategories = Wishcategory.objects.filter(user=request.user)
        #Products = Product.objects.filter(address=address, product_category__in=wishcategories)
        products = Product.objects.filter(address=address_id).prefetch_related(Prefetch('productimage_set', queryset = ProductImage.objects.all(), to_attr='productimage_list'))

        result= [{
            "id"               : item.id,
            "imgSrc"           : item.productimage_list[0].image_url, 
            "title"            : item.name,
            "price"            : item.price,
            "order_status"     : item.order_status.name,
            }for item in products]

        return JsonResponse({"message" : "SUCCESS", "sellerItemsData" : result}, status = 200) 

class WishlistView(View):
    def post(self, request, product_id):
        product_ins = Product.objects.get(id=product_id)
        user_ins = User.objects.get(id=2) #임시로 2
        Wishlist.objects.create(is_liked=True, product = product_ins, user = user_ins)
        return JsonResponse({"message" : "SUCCESS"}, status = 200)
        