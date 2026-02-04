from rest_framework import serializers
from .models import TimeSlot


class SlotSerializer(serializers.ModelSerializer):
    time = serializers.SerializerMethodField()
    category = serializers.CharField(source='category.name')
    status = serializers.SerializerMethodField()

    class Meta:
        model = TimeSlot
        fields = ['id', 'time', 'category', 'status']

    def get_time(self, obj):
        return f"{obj.start_time.strftime('%I:%M %p')} – {obj.end_time.strftime('%I:%M %p')}"

    def get_status(self, obj):
        request = self.context.get('request')

        if obj.booked_by is None:
            return 'available'
        if request and getattr(request, 'user', None) and request.user.is_authenticated and obj.booked_by == request.user:
            return 'mine'

        return 'booked'

