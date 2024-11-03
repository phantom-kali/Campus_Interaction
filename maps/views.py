from django.shortcuts import render
from django.http import JsonResponse
from .models import Landmark
from django.views import View
import math


def maps(request):
    return render(request, "maps/base.html")


def search_building(request):
    query = request.GET.get("query", "").strip()
    if query:
        buildings = Landmark.objects.filter(name__icontains=query)
        data = [
            {
                "name": b.name,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "description": b.description,
            }
            for b in buildings
        ]
        return JsonResponse(data, safe=False)
    return JsonResponse([], safe=False)


class LandmarksNearby(View):
    def get(self, request):
        try:
            latitude = float(request.GET.get("lat"))
            longitude = float(request.GET.get("lng"))
            radius = float(request.GET.get("radius", 5))
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid parameters"}, status=400)

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            d_lat = math.radians(lat2 - lat1)
            d_lon = math.radians(lon2 - lon1)
            a = (
                math.sin(d_lat / 2) ** 2
                + math.cos(math.radians(lat1))
                * math.cos(math.radians(lat2))
                * math.sin(d_lon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            return R * c

        landmarks = []
        for lm in Landmark.objects.all():
            distance = haversine(
                latitude, longitude, float(lm.latitude), float(lm.longitude)
            )
            if distance <= radius:
                landmarks.append(
                    {
                        "name": lm.name,
                        "latitude": lm.latitude,
                        "longitude": lm.longitude,
                        "description": lm.description,
                        "distance": round(distance, 2),
                    }
                )

        return JsonResponse(landmarks, safe=False)
