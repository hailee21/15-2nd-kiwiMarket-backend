from django.urls   import path
from product.views import (
    ProductDetailView, 
    ProductListView, 
    SellerItemsView, 
    RelatedProductView, 
    ProductUploadView,
    CommentDetailView,
    CommentUploadView,
    WishlistView
)
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [path('/detail/<int:product_id>', ProductDetailView.as_view()),
               path('/<int:address_id>', ProductListView.as_view()),
               path('/selleritems/<int:uploader_id>', SellerItemsView.as_view()),
               path('/productupload/<int:address_id>', ProductUploadView.as_view()),
               path('/relateditems/<int:address_id>', RelatedProductView.as_view()),
               path('/comment/<int:product_id>', CommentDetailView.as_view()),
               path('/commentupload/<int:product_id>', CommentUploadView.as_view()),
               path('/wishlist/<int:product_id>', WishlistView.as_view()),               
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_ROOT, document_root=settings.MEDIA_ROOT)
