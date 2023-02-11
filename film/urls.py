from rest_framework import routers
from .views import FilmViewSet

router = routers.SimpleRouter()
router.register('films', FilmViewSet)
urlpatterns = router.urls
