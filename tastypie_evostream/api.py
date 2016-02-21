from django.http import Http404
from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource
from evostream import EvoStreamException
from evostream.commands import list_streams, get_stream_info, list_config, \
    remove_config, pull_stream, shutdown_stream


class StreamResponse(object):
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


class StreamResource(Resource):
    appName = fields.CharField('appName')
    audio = fields.DictField('audio')
    bandwidth = fields.IntegerField('bandwidth')
    connectionType = fields.IntegerField('connectionType')
    creationTimestamp = fields.FloatField('creationTimestamp')
    edgePid = fields.IntegerField('edgePid', null=True)
    ip = fields.CharField('ip')
    name = fields.CharField('name')
    outStreamsUniqueIds = fields.ListField('outStreamsUniqueIds', null=True)
    port = fields.IntegerField('port')
    pullSettings = fields.DictField('pullSettings', null=True)
    queryTimestamp = fields.FloatField('queryTimestamp')
    type = fields.CharField('type')
    typeNumeric = fields.IntegerField('typeNumeric')
    uniqueId = fields.IntegerField('uniqueId')
    upTime = fields.FloatField('upTime')
    video = fields.DictField('video')

    class Meta:
        resource_name = 'stream'
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'delete']
        object_class = StreamResponse
        include_resource_uri = False
        detail_uri_name = 'uniqueId'

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs.update({
                self._meta.detail_uri_name: getattr(bundle_or_obj.obj,
                                                    self._meta.detail_uri_name)
            })
        else:
            kwargs.update({
                self._meta.detail_uri_name: getattr(bundle_or_obj,
                                                    self._meta.detail_uri_name)
            })

        return kwargs

    def obj_get_list(self, bundle, **kwargs):
        """
        Get streams list
        """
        streams = list_streams()

        if streams is None:
            return []

        streams = [StreamResponse(**stream) for stream in streams]

        return streams

    def obj_get(self, bundle, **kwargs):
        """
        Get stream info
        """
        unique_id = kwargs.get('uniqueId')
        if isinstance(unique_id, int):
            stream = get_stream_info(id=unique_id)

            if stream is not None:
                return StreamResponse(**stream)

        try:
            streams = list_streams()
        except EvoStreamException as ex:
            raise Http404('EvoStream error: %s' % ex)

        if streams is None:
            raise Http404('Stream with id=%s does not exists!' % unique_id)

        for stream in streams:
            if stream['name'] == unique_id:
                return StreamResponse(**stream)
            try:
                if stream['pullSettings']['localStreamName'] == unique_id:
                    return StreamResponse(**stream)
            except KeyError:
                pass

        raise Http404('Stream with id=%s does not exists!' % unique_id)

    def obj_create(self, bundle, **kwargs):
        """
        Create a stream
        """
        streams = list_streams()
        if streams is not None:
            for stream in streams:
                if stream['name'] == bundle.data.get('name'):
                    return None

        configs = list_config()
        if configs is not None:
            for config in configs['pull']:
                if config['localStreamName'] == bundle.data.get('name'):
                    remove_config(id=config['configId'])

        try:
            pull_stream(uri=bundle.data.get('rtsp'),
                        localStreamName=bundle.data.get('name'))
        except EvoStreamException as ex:
            raise Http404('EvoStream error: %s' % ex)

        return None

    def obj_delete(self, bundle, **kwargs):
        """
        Delete a stream
        """
        params = {}

        if kwargs.get('uniqueId'):
            params['id'] = kwargs.get('uniqueId')
        if kwargs.get('name'):
            params['name'] = kwargs.get('name')

        shutdown_stream(**params)
