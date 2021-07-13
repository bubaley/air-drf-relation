from air_drf_relation.nested_fields_factory import NestedSaveFactory
from air_drf_relation.serializers import AirModelSerializer
from rest_framework.serializers import ModelSerializer
from .models import School, Cabinet, Parent, Floor


class CabinetWithoutSchoolSerializer(ModelSerializer):
    class Meta:
        model = Cabinet
        fields = ('id', 'name', 'code')


class CabinetWithSchoolSerializer(AirModelSerializer):
    class Meta:
        model = Cabinet
        fields = ('id', 'name', 'code', 'school')


class SchoolDefaultNestedSerializer(ModelSerializer):
    cabinets = CabinetWithoutSchoolSerializer(many=True)

    class Meta:
        model = School
        fields = ('id', 'name', 'cabinets')

    def create(self, validated_data):
        cabinets = validated_data.pop('cabinets', [])
        instance = School.objects.create(**validated_data)
        for el in cabinets:
            Cabinet.objects.create(**el, school=instance)
        return instance

    def update(self, instance: School, validated_data):
        cabinets = validated_data.pop('cabinets', [])
        instance.cabinets.all().delete()
        instance.__dict__.update(validated_data)
        instance.save()
        for el in cabinets:
            Cabinet.objects.create(**el, school=instance)
        return instance


class SchoolCustomNestedSerializer(ModelSerializer):
    cabinets = CabinetWithoutSchoolSerializer(many=True)

    class Meta:
        model = School
        fields = ('id', 'name', 'cabinets')

    def save_nested(self, validated_data, instance=None):
        factory = NestedSaveFactory(serializer=self, nested_save_fields=['cabinets'])
        factory.set_data(validated_data=validated_data, instance=instance)
        return factory.save_instance().save_nested_fields().instance

    def create(self, validated_data):
        return self.save_nested(validated_data=validated_data)

    def update(self, instance, validated_data):
        return self.save_nested(validated_data=validated_data, instance=instance)


class SchoolAutoNestedSerializer(AirModelSerializer):
    cabinets = CabinetWithSchoolSerializer(many=True)

    class Meta:
        model = School
        fields = ('id', 'name', 'cabinets')
        nested_save_fields = ('cabinets',)


class FloorWithSchoolSerializer(AirModelSerializer):
    class Meta:
        model = Floor
        fields = ('uuid', 'name', 'school')


class SchoolAutoNestedWithFloorSerializer(AirModelSerializer):
    floors = FloorWithSchoolSerializer(many=True)

    class Meta:
        model = School
        fields = ('id', 'name', 'floors')
        nested_save_fields = ('floors',)


class ParentCreateByPkSerializer(AirModelSerializer):
    class Meta:
        model = Parent
        fields = ('uuid', 'name')
