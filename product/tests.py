import json
import bcrypt
import datetime

from .models import (
    Product,
    ProductImage,
    MainCategory,
    ProductCategory,
    ProductComment
)

from user.models import(
    User,
    Address,
    OrderStatus,
    Wishlist
)

from django.test      import TestCase, Client
from unittest.mock    import MagicMock, Mock
from django.db.models import Prefetch, Count
from django.utils     import timezone
from freezegun        import freeze_time

TestCase.maxDiff = None

@freeze_time("2021-01-04T09:26:14.946000+00:00")
class ProductListTest(TestCase):
    def setUp(self):
        a1 = ProductCategory(name="여성의류")
        a1.save()

        a1 = OrderStatus(name='판매중')
        a1.save()

        User.objects.create(
            id           = 1,
            phone_number = '01063510445',
            nickname     = '승연',
            anonymous    = False,
            created_at   = 0000
        )

        Address.objects.create(
            id        = 1817,
            code      = 1129011100,
            longitude = 127.007942,
            latitude  = 37.585059,
            address1  = '서울특별시',
            address2  = '성북구',
            address3  = '삼선동1가'
        )

        Product.objects.create(
            id               = 1,
            name             = "멋진 티셔츠 팝니다",
            price            = 10000,
            product_category = ProductCategory.objects.get(name='여성의류'),
            uploader         = User.objects.get(id=1),
            description      = "몇번 안입었어요",
            access_range     = 4,
            address          = Address.objects.get(id=1817),
            order_status     = OrderStatus.objects.get(name='판매중'),
            )

        ProductImage.objects.create(
            id        = 1,
            image_url = "www.lyl.com",
            product   = Product.objects.get(id=1)
        )

        Wishlist.objects.create(
            is_liked = True,
            product  = Product.objects.get(id=1),
            user     = User.objects.get(id=1)
        )

    def tearDown(self):
        ProductCategory.objects.all().delete()
        OrderStatus.objects.all().delete()
        User.objects.all().delete()
        Address.objects.all().delete()
        Product.objects.all().delete()
        ProductImage.objects.all().delete()
        Wishlist.objects.all().delete()

    def test_product_list_get_success(self):
        client   = Client()
        response = client.get('/product/1817')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message" : "SUCCESS", 
            "productList" :[
                {'commentCount': 0,
                'imgSrc'       : 'www.lyl.com',
                'itemId'       : 1,
                'order_status' : '판매중',
                'postedTime'   : '2021-01-04T09:26:14.946000+00:00',
                'price'        : 10000,
                'title'        : '멋진 티셔츠 팝니다',
                'townName'     : '성북구 삼선동1가',
                'viewed'       : None,
                'wishCount'    : 1
                }]})

    def test_product_list_get_fail(self):
        client   = Client()
        response = client.get('/product/1')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            "message" : "NO_PRODUCT"
            })

    def test_product_list_get_not_found(self):
        client   = Client()
        response = client.get('/product?product=책')
        self.assertEqual(response.status_code, 404)
        


@freeze_time("2021-01-04T09:26:14.946000+00:00")
class ProductDetailTest(TestCase):
    def setUp(self):
        a1 = ProductCategory(name="여성의류")
        a1.save()

        a1 = OrderStatus(name='판매중')
        a1.save()

        User.objects.create(
            id           = 1,
            phone_number = '01063510445',
            nickname     = '승연',
            anonymous    = False,
            created_at   = 0000
        )

        Address.objects.create(
            id        = 1817,
            code      = 1129011100,
            longitude = 127.007942,
            latitude  = 37.585059,
            address1  = '서울특별시',
            address2  = '성북구',
            address3  =  '삼선동1가'
        )

        Product.objects.create(
            id               = 1,
            name             = "멋진 티셔츠 팝니다",
            price            = 10000,
            product_category = ProductCategory.objects.get(name='여성의류'),
            uploader         = User.objects.get(id=1),
            description      = "몇번 안입었어요",
            access_range     = 4,
            address          = Address.objects.get(id=1817),
            order_status     = OrderStatus.objects.get(name='판매중'),
            viewed           = 3,
        )

        ProductImage.objects.create(
            id        = 1,
            image_url = "www.lyl.com",
            product   = Product.objects.get(id=1)
        )

        Wishlist.objects.create(
            is_liked = True,
            product  = Product.objects.get(id=1),
            user     = User.objects.get(id=1)
        )

    def tearDown(self):
        ProductCategory.objects.all().delete()
        OrderStatus.objects.all().delete()
        User.objects.all().delete()
        Address.objects.all().delete()
        Product.objects.all().delete()
        ProductImage.objects.all().delete()
        Wishlist.objects.all().delete()

    def test_product_detail_get_success(self):
        client   = Client()
        response = client.get('/product/detail/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message" : "SUCCESS", 
            "itemDetailData" : 
            {'productdetail': [
                {'category'    : '여성의류',
                'commentCount' : 0,
                'description'  : '몇번 안입었어요',
                'hits'         : 4,
                'imgSrcList'   : ['www.lyl.com'],
                'itemId'       : 1,
                'order_status' : '판매중',
                'postedTime'   : '2021-01-04T09:26:14.946000+00:00',
                'price'        : 10000,
                'title'        : '멋진 티셔츠 팝니다',
                'wishCount'    : 1}],
            'sellerdata': [
                {'mannerTemperature': 36.5,
                'seller'            : '승연',
                'seller_id'         : 1,
                'seller_profilepic' : '사진 데이터가 없음',
                'townName'          : '성북구 삼선동1가',
                'towncode'          : 1817}]}})

    def test_product_detail_get_fail(self):
        client   = Client()
        response = client.get('/product/detail/2')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            "message" : "NO_PRODUCT"
            })

    def test_product_detail_list_get_not_found(self):
        client   = Client()
        response = client.get('/product/detail?product=책')
        self.assertEqual(response.status_code, 404)

class SellerItemsTest(TestCase):
    def setUp(self):
        a1 = ProductCategory(name="여성의류")
        a1.save()
        a2 = ProductCategory(name="게임/취미")
        a2.save()

        a1 = OrderStatus(name='판매중')
        a1.save()

        User.objects.create(
            id           = 1,
            phone_number = '01063510445',
            nickname     = '승연',
            anonymous    = False,
            created_at   = 0000
        )

        Address.objects.create(
            id        = 1817,
            code      = 1129011100,
            longitude = 127.007942,
            latitude  = 37.585059,
            address1  = '서울특별시',
            address2  = '성북구',
            address3  =  '삼선동1가'
        )

        Product.objects.create(
            id               = 1,
            name             = "멋진 티셔츠 팝니다",
            price            = 10000,
            product_category = ProductCategory.objects.get(name='여성의류'),
            uploader         = User.objects.get(id=1),
            description      = "몇번 안입었어요",
            access_range     = 4,
            address          = Address.objects.get(id=1817),
            order_status     = OrderStatus.objects.get(name='판매중'),
            )

        Product.objects.create(
            id               = 2,
            name             = "두뇌능력 향상 보드게임",
            price            = 10000,
            product_category = ProductCategory.objects.get(name='게임/취미'),
            uploader         = User.objects.get(id=1),
            description      = "딸아이가 좋아했던 보드게임입니다.",
            access_range     = 4,
            address          = Address.objects.get(id=1817),
            order_status     = OrderStatus.objects.get(name='판매중'),
            )

        ProductImage.objects.create(
            id        = 1,
            image_url = "www.lyl.com",
            product   = Product.objects.get(id=1)
        )

        ProductImage.objects.create(
            id        = 2,
            image_url = "www.lyl.com",
            product   = Product.objects.get(id=2)
        )

        Wishlist.objects.create(
            is_liked = True,
            product  = Product.objects.get(id=1),
            user     = User.objects.get(id=1)
        )

    def tearDown(self):
        ProductCategory.objects.all().delete()
        OrderStatus.objects.all().delete()
        User.objects.all().delete()
        Address.objects.all().delete()
        Product.objects.all().delete()
        ProductImage.objects.all().delete()
        Wishlist.objects.all().delete()

    def test_seller_items_list_get_success(self):
        client   = Client()
        response = client.get('/product/selleritems/1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "message" : "SUCCESS", 
            "sellerItemsData" : [
            {
            "id"           : 1,
            "imgSrc"       : "www.lyl.com",
            "title"        : "멋진 티셔츠 팝니다",
            "price"        : 10000,
            "order_status" : '판매중'
            },
            {
            "id"           : 2,
            "imgSrc"       : "www.lyl.com",
            "title"        : "두뇌능력 향상 보드게임",
            "price"        : 10000,
            "order_status" : '판매중'
            }]})

    def test_seller_items_list_get_fail(self):
        client   = Client()
        response = client.get('/product/selleritems/2')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {
            "message" : "NO_SELLING_PRODUCT"
            })

    def test_seller_items_list_get_not_found(self):
        client   = Client()
        response = client.get('/product/selleritems?seller=승연')
        self.assertEqual(response.status_code, 404)

