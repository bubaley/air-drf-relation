from air_drf_relation.serializers import AirModelSerializer
from air_drf_relation.fields import AirRelatedField
from .models import Table, Material, Leg


class MaterialSerializer(AirModelSerializer):
    class Meta:
        model = Material
        fields = ('company',)


class TableSerializer(AirModelSerializer):
    material = AirRelatedField(MaterialSerializer, as_serializer=True)

    class Meta:
        model = Table
        fields = ('material', 'legs', 'color')


class LegSerializer(AirModelSerializer):
    class Meta:
        model = Leg
        fields = ('id', 'name', 'color')


class TableWithLegsSerializer(AirModelSerializer):
    legs = AirRelatedField(LegSerializer, many=True, as_serializer=True)

    class Meta:
        model = Table
        fields = ('legs', 'color', 'material')
