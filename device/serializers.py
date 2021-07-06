from air_drf_relation.serializers import AirModelSerializer
from .models import Device


class DeviceWithoutActionsSerializer(AirModelSerializer):
    class Meta:
        model = Device
        fields = ('id', 'name', 'code', 'text', 'model')
        hidden_fields = ('name', 'code')
        read_only_fields = ('text', 'model')


class DeviceWithReadOnlyActionsSerializer(AirModelSerializer):
    class Meta:
        model = Device
        fields = ('id', 'name', 'code', 'text', 'model')
        action_read_only_fields = {
            'create': ('name', 'code'),
            '_': ('model',)
        }


class DeviceWithHiddenActionsSerializer(AirModelSerializer):
    class Meta:
        model = Device
        fields = ('id', 'name', 'code', 'text', 'model')
        action_hidden_fields = {
            'update': ('id',),
            '_': ('name', 'code', 'text', 'model')
        }
