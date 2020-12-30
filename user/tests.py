import unittest
import json
import datetime

from django.test import TestCase, Client

from .models import User, AuthSms, FullAddress, Address
from product.models import Product, ProductImage
from my_settings import (
    service_id, 
    secretKey, 
    AUTH_ACCESS_KEY, 
    AUTH_SECRET_KEY, 
    SMS_SEND_PHONE_NUMBER, 
    SECRET_KEY, 
    ALGORITHM
)


class UserTest(TestCase):

    def setUp(self):
        User.objects.create(
            phone_number='01000000000',
            nickname='테식이',
            email='test@naver.com'
        )
        Product.objects.create(
            name='상품상품',
            price=10000,
            description='설명설명',
            order_status_id=1
        )
        ProductImage.objects.create(
            product_id=1,
            image_url='https://dnvefa72aowie.cloudfront.net/capri/smb/202012/a80802f0c8ea1c6be4de66c6ff44f809210604961dd5f7604e.jpeg?q=95&s=1440x1440&t=inside'
        )

    def tearDown(self):
        print('end')
        
    def test_smsverificationview_post_send_sms(self):
        client = Client()
        data = {
            'phone_number' : '01067841882'
        }

        response = client.post('/user/smscheck', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})

    def test_verificationcodeview_post_auth_number_check(self):
        client = Client()
        data = {
            'phone_number' : '01067841882',
            'auth_number'  : AuthSms.objects.get(phone_number='01067841882').auth_number 
        }

        response = client.post('/user/checknum', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message': 'SIGNUP', 'token': ''})

    def test_checknicknameview_post_nickname_check(self):
        client = Client()
        data = {
            'nickname' : '김영이'
        }

        response = client.post('/user/checknickname', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})


    def test_signupview_post_create(self):
        client = Client()
        data = {
            'phone_number'    : '01067841882',
            'nickname'        : '김영이',
            'email'           : 'eee@naver.com',
            'address_code'    : '1111017600'
        }

        self.token = jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)

        response = client.post('/user/signup', json.dumps(data), content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'message' : 'SUCCESS', 'token': self.token})

    def test_signinview_post(self):
        client = Client()
        data = {
            'phone_number' : '01063510445',
            'auth_number'  : AuthSms.objects.get(phone_number='01063510445').auth_number 
        }

        self.token = jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)

        response = client.post('/user/smscheck', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message' : 'SIGNIN', 'token': self.token})

    def test_selectmyaddressview_post_create_fulladdress(self):
        client = Client()
        headers = {'Authorization': jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)}
        data = {
            'address_code'  : '1111017600'
        }

        response = client.post('/user/selectmyaddress', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})

    def test_deletemyaddressview_post_delete_fulladdress(self):
        client = Client()
        headers = {'Authorization': jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)}
        data = {
            'address_code'  : '1111017600'
        }

        response = client.post('/user/deletemyaddress', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})

    def test_userprofileview_get_select_profile(self):
        client = Client()
        headers = {'Authorization': jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)}

        response = client.get('/user/profile',  content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})
    
    def test_saleshistoryview_get_sales_list(self):
        client = Client()
        headers = {'Authorization': jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)}

        response = client.post('/user/saleshistory?order_status_id=1', content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})
    
    def test_ChangeOrderStatusView_update_sales_status(self):
        client = Client()
        headers = {'Authorization': jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)}
        data = {
            'order_status_id' : 2
        }

        response = client.post('/user/changestatus/1', json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'message' : 'SUCCESS'})
    


if __name__ == '__main__':
    unittest.main()