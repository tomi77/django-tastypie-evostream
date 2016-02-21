from django.conf.urls import patterns, include, url
from tastypie.api import Api

from tastypie_evostream.api import StreamResource


tastypie_evostream_api = Api()

tastypie_evostream_api.register(StreamResource())

urlpatterns = patterns(
    '',
    url(r'', include(tastypie_evostream_api.urls)),
)