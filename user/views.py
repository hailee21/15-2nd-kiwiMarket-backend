from django.shortcuts import render

# Create your views here.
import json, jwt
import hashlib
import hmac
import base64
import requests
import time
import datetime
from random import randint


from django.views               import View
from django.http                import JsonResponse, HttpResponse
from rest_framework             import status
from rest_framework.response    import Response
from rest_framework.views       import APIView
from django.core.exceptions     import ValidationError
from django.db                  import IntegrityError, transaction

from user.utils         import login_check
from my_settings        import (service_id, secretKey, AUTH_ACCESS_KEY, AUTH_SECRET_KEY, SMS_SEND_PHONE_NUMBER, SECRET_KEY, ALGORITHM)
from user.models        import (
                                User,
                                AuthSms,
                                FullAddress,
                                Address,
                                OrderStatus,
                            )
from product.models     import(
                                Product,
                                ProductImage
                            )

# SMS 인증 (1) - 인증코드 발송
class SMSVerificationView(View):
    def send_verification(self, phone_number, auth_number):
        # 네이버 클라우드 플랫폼 주소 입력
        SMS_URL    = 'https://sens.apigw.ntruss.com/sms/v2/services/'+f'{service_id}'+'/messages'
        
        # time.time()*1000은 1970년 1월 1일 00:00:00 협정 세계시(UTC)부터의 경과 시간을 밀리초(Millisecond)단위로 나타낸 것
        ## (API Gateway 서버와 시간 차가 5분 이상 나는 경우 유효하지 않은 요청으로 처리하기 위해 필요)
        timestamp  = str(int(time.time()*1000))

        secret_key = bytes(AUTH_SECRET_KEY, 'utf-8')
        
        # 요청보내기 위한 준비
        method  = 'POST'
        uri     = '/sms/v2/services/'+f'{service_id}'+'/messages'
        message = method + ' ' + uri + '\n' + timestamp + '\n' + AUTH_ACCESS_KEY
     
        # 암호화를 위해 bytes type으로 인코딩
        message = bytes(message, 'utf-8')

        # 위에서 생성한 StringToSign(message)를 HmacSHA256 알고리즘으로 암호화한 후
        # base64로 인코딩해서 signingKey 생성
        signingKey = base64.b64encode(
                        hmac.new(secret_key, message, digestmod=hashlib.sha256).digest()
                    )
        
        # 요청 헤더
        headers    = {
            'Content-Type'             : 'application/json; charset=utf-8',
            'x-ncp-apigw-timestamp'    : timestamp,
            'x-ncp-iam-access-key'     : AUTH_ACCESS_KEY,
            'x-ncp-apigw-signature-v2' : signingKey,
        }

        # 요청 바디
        body       = {
            'type'        : 'SMS',
            'contentType' : 'COMM',
            'countryCode' : '82',
            'from'        : f'{SMS_SEND_PHONE_NUMBER}',
            'content'     : f'키위마켓입니당>< \n인증번호 [{auth_number}]를 입력해주세요.',
            'messages'    : [
                {
                    'to' : phone_number
                }
            ]
        }

        ## 만든 바디를 json 형태로 변환한 뒤
        encoded_data = json.dumps(body)
        # 헤더와 함께 post 메소드로 SMS 전송 url에 요청을 보낸다.
        res          = requests.post(SMS_URL, headers=headers, data=encoded_data)
        return HttpResponse(res.status_code)

    def post(self, request):
        try:
            data                = json.loads(request.body)
            phone_number        = data['phone_number']

            # 인증번호 랜덤 생성
            auth_number = str(randint(100000, 999999))
            with transaction.atomic():
                # 휴대전화 번호가 존재하는지 여부 확인한 뒤 작업.
                AuthSms.objects.update_or_create(
                    phone_number = phone_number,
                    defaults     = {
                        'phone_number': phone_number,
                        'auth_number' : auth_number
                    }
                )

                # 휴대전화번호와 인증번호를 담아 같은 클래스 내 send_verification 호출
                self.send_verification(
                    phone_number    = phone_number,
                    auth_number     = auth_number
                )
            return JsonResponse({'message' : 'SUCCESS'}, status=201)
        except KeyError:
            return JsonResponse({'message' : 'INVALID_KEY'}, status=400)
        except IntegrityError:
            handle_exception()

# SMS 인증(2) - 인증코드 인증 및 회원여부 체크
class VerificationCodeView(View):
    def signInCheck(self, phone_number):
        user    = User.objects.filter(phone_number=phone_number)
        token   = ''
        if user:
            token = jwt.encode({'id':user[0].id}, SECRET_KEY, ALGORITHM)
        return token

    def post(self, request):
        try:
            data = json.loads(request.body)
            if AuthSms.objects.filter(phone_number=data['phone_number']).exists():
                code = AuthSms.objects.get(phone_number = data['phone_number'])
                if code.auth_number == int(data['auth_number']):
                    token = VerificationCodeView.signInCheck(self, str(data['phone_number']))
                    if token != '':
                        return JsonResponse({'message': 'SIGNIN', 'token': token}, status=200)
                    code.delete()
                    return JsonResponse({'message': 'SIGNUP', 'token': token}, status=200)
            return JsonResponse({'message': 'DENY'}, status=400)                
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

# 회원가입 전, 가입가능한 정보(닉네임)인지 체크
class CheckNickNameView(View):
    def post(self, request):
        try:
            data        = json.loads(request.body)
            nickname    = data['nickname']

            if User.objects.filter(nickname = nickname).exists():
                return JsonResponse({'message': 'DUPLICATED_NICKNAME'}, status=409)    
            return JsonResponse({'message': 'SUCCESS'}, status=200)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

# 회원가입 및 토큰 발행
class SignUpView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)

            phone_number    = data['phone_number']
            nickname        = data['nickname']
            email           = data['email']
            address_code    = data['address_code']
            # 지역코드 정보 추가

            if str(phone_number[:3]) != '010':
                return JsonResponse({'message': 'INVALID_PHONENUMBER'}, status=400)
            if len(str(phone_number)) != 11:
                return JsonResponse({'message': 'INVALID_PHONENUMBER_LENGTH'}, status=400)
            if User.objects.filter(phone_number = phone_number).exists():
                return JsonResponse({'message': 'DUPLICATED_PHONENUMBER'}, status=409)
            if User.objects.filter(nickname = nickname).exists():
                return JsonResponse({'message': 'DUPLICATED_NICKNAME'}, status=409)     
            # if User.objects.filter(email = email).exists():
            #     return JsonResponse({'message': 'DUPLICATED_EMAIL'}, status=409)        
            if transaction.atomic():
                # User에 회원데이터 생성
                User.objects.create(
                    phone_number    = phone_number,
                    nickname        = nickname,
                    email           = email,
                )
                # FullAddress에 동네 생성
                FullAddress.objects.create(
                    user_id           = User.objects.latest('id').id,
                    full_address_id   = Address.objects.get(code=data['address_code']).id,
                    created_at        = datetime.datetime.now()
                )
            token = jwt.encode({'id':User.objects.latest('id').id}, SECRET_KEY, ALGORITHM)
            return JsonResponse({'message': 'SUCCESS', 'token': token}, status=201)
        except ValidationError:
            return JsonResponse({'message': 'INVALID_PHONENUMBER'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)
        except IntegrityError:
            handle_exception()

# 동네 조회
class SelectMyAddressView(View):
    @login_check
    def get(self, request):
        try:
            data = FullAddress.objects.select_related('full_address').filter(user_id = request.user.id)
            address_list = [{
                'id'            : address.id,
                'user_id'       : address.user_id,
                'address_code'  : address.full_address.code,
                'address_name'  : address.full_address.neighborhood
            } for address in data]
            return JsonResponse({'message': 'SUCCESS', 'address_list': address_list}, status=200)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

# 동네별 근처 동네 리스트 조회
class GetNearAddressView(View):
    @login_check
    def get(self, request, code):
        try:
            address_code = str(code)[:5]
            data = Address.objects.filter(code__startswith=address_code)
            near_address_list = [{
                'id'        : near_address.id,
                'code'      : near_address.code,
                'longitude' : near_address.longitude,
                'latitude'  : near_address.latitude,
                'address'   : near_address.district + ' ' + near_address.neighborhood
            } for near_address in data]
            return JsonResponse({'message': 'SUCCESS', 'near_address_list': near_address_list}, status=200)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

# 동네 등록
class AddMyAddressView(View):
    @login_check
    def post(self, request):
        try:
            data = json.loads(request.body)
            FullAddress.objects.create(
                user_id           = request.user.id,
                full_address_id   = Address.objects.get(code=data['address_code']).id
            )
            return JsonResponse({'message': 'SUCCESS'}, status=201)
        except ValidationError:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

# 동네 삭제
class DeleteMyAddressView(View):
    @login_check
    def post(self, request):
        try:
            data = json.loads(request.body)
            FullAddress.objects.filter(
                user_id           = request.user.id,
                full_address_id   = Address.objects.get(code=data['address_code']).id
            ).delete()
            return JsonResponse({'message': 'SUCCESS'}, status=204)
        except ValidationError:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)

# 나의 당근 메인화면
class UserProfileView(View):
    @login_check
    def get(self, request):
        try:
            data = User.objects.get(id=request.user.id)
            address_data = FullAddress.objects.select_related('full_address').filter(user_id=request.user.id).first()

            user = {
                'user_id'           : '#'+str(data.id),
                'nickname'          : data.nickname,
                'profile_picture'   : data.profile_picture,
                'address_name'      : address_data.full_address.neighborhood,
                'address_code'      : address_data.full_address.id
            }

            return JsonResponse({'message': 'SUCCESS', 'user': user}, status=200)
        except ValidationError:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)
        except User.DoesNotExist:
            return JsonResponse({'message' : 'USER_DOES_NOT_EXIST'}, status = 404)
        except FullAddress.DoesNotExist:
            return JsonResponse({'message' : 'FULL_ADDRESS_DOES_NOT_EXIST'}, status = 404)

# 프로필 수정

# 프로필 보기

# 판매내역
class SalesHistoryView(View):
    @login_check
    def get(self, request):
        try:
            order_status_id    = request.GET.get('order_status_id', 1)
            sales_list = [{
                'id'                : item.id,
                'name'              : item.name,
                'address_code'      : item.address_id,
                'address_name'      : Address.objects.get(id=item.address_id).region + ' ' + Address.objects.get(id=item.address_id).district,
                'price'             : item.price,
                'order_status_id'   : item.order_status_id,
                'order_status_name' : OrderStatus.objects.get(id=item.order_status_id).name,
                'images'            : list(ProductImage.objects.filter(product_id=item.id).values_list('image_url', flat=True))
                # ProductComment 테이블 생성 후 추가하기
                # 상품 좋아요 추가하기
            } for item in Product.objects.filter(uploader_id=request.user.id, order_status_id=order_status_id)]

            return JsonResponse({'message': 'SUCCESS', 'sales_list': sales_list}, status=200)
        except ValidationError:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)
        except Address.DoesNotExist:
            return JsonResponse({'message' : 'ADDRESS_DOES_NOT_EXIST'}, status = 404)
        except OrderStatus.DoesNotExist:
            return JsonResponse({'message' : 'ORDER_STATUS_DOES_NOT_EXIST'}, status = 404)
        except ProductImage.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_IMAGE_DOES_NOT_EXIST'}, status = 404)
        except Product.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_DOES_NOT_EXIST'}, status = 404)

# 판매 상태 변경
class ChangeOrderStatusView(View):
    @login_check
    def post(self, request, product_id):
        try:
            data = json.loads(request.body)
            if Product.objects.filter(id=product_id).exists():
                Product.objects.filter(id=product_id).update(order_status_id=data['order_status_id'])
            return JsonResponse({'message': 'SUCCESS'}, status=200)
        except ValidationError:
            return JsonResponse({'message': 'INVALID_USER'}, status=400)
        except KeyError:
            return JsonResponse({'message': 'KEY_ERROR'}, status=400)
        except Product.DoesNotExist:
            return JsonResponse({'message' : 'PRODUCT_DOES_NOT_EXIST'}, status = 404)


# 구매내역

# 관심목록

