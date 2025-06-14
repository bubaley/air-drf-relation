from rest_framework.relations import ManyRelatedField, PrimaryKeyRelatedField

from air_drf_relation.fields import AirRelatedField
from air_drf_relation.serializers import AirEmptySerializer, AirModelSerializer

from .models import Leg, Material, Table


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


class TableSimpleSerializer(AirModelSerializer):
    class Meta:
        model = Table
        fields = ('legs', 'color', 'material')


class CustomSerializer(AirEmptySerializer):
    leg = PrimaryKeyRelatedField(queryset=Leg.objects)
    legs = ManyRelatedField(child_relation=PrimaryKeyRelatedField(queryset=Leg.objects))
    tables = TableSimpleSerializer(many=True)
    material = PrimaryKeyRelatedField(queryset=Material.objects)
