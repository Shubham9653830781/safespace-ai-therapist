import googlemaps

try:
    from backend.config import GOOGLE_MAPS_API_KEY
except ImportError:
    from config import GOOGLE_MAPS_API_KEY
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

def find_nearby_therapists_by_location(location: str) -> str:
    if not gmaps:
        import urllib.parse
        encoded_loc = urllib.parse.quote(location.strip())
        return (
            f"Direct Google Maps lookup is currently unconfigured. Here are immediate directories and verified contact numbers for {location}:\n\n"
            f"1. **Psychology Today Therapist Directory**: https://www.psychologytoday.com/us/therapists/{encoded_loc}\n"
            f"2. **GoodTherapy Directory**: https://www.goodtherapy.org/therapists/{encoded_loc}\n"
            f"3. **SAMHSA National Mental Health Helpline (24/7, Free)**: 1-800-662-4357\n"
            f"4. **988 Suicide & Crisis Lifeline**: Call or text 988\n"
            f"5. **Crisis Text Line**: Text HOME to 741741\n"
            f"6. **International Helpline Directory**: https://findahelpline.com/"
        )
    try:
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return f"Could not find coordinates for '{location}'."
        lat_lng = geocode_result[0]['geometry']['location']
        lat, lng = lat_lng['lat'], lat_lng['lng']
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=5000,
            keyword="Psychotherapist"
        )
        output = [f"Therapists near {location}:"]
        top_results = places_result.get('results', [])[:5]
        for place in top_results:
            name = place.get("name", "Unknown")
            address = place.get("vicinity", "Address not available")
            phone = "Phone not available"
            place_id = place.get("place_id")
            if place_id:
                try:
                    details = gmaps.place(place_id=place_id, fields=["formatted_phone_number"])
                    phone = details.get("result", {}).get("formatted_phone_number", "Phone not available")
                except Exception:
                    pass
            output.append(f"- **{name}** | {address} | 📞 {phone}")

        return "\n".join(output)
    except Exception as e:
        import urllib.parse
        encoded_loc = urllib.parse.quote(location.strip())
        return (
            f"Google Maps service notice: {e}\n\n"
            f"Here are immediate direct directories and contact numbers for therapists near {location}:\n\n"
            f"1. **Psychology Today Therapist Directory**: https://www.psychologytoday.com/us/therapists/{encoded_loc}\n"
            f"2. **GoodTherapy Directory**: https://www.goodtherapy.org/therapists/{encoded_loc}\n"
            f"3. **SAMHSA National Mental Health Helpline (24/7, Free)**: 1-800-662-4357\n"
            f"4. **988 Suicide & Crisis Lifeline**: Call or text 988\n"
            f"5. **Crisis Text Line**: Text HOME to 741741\n"
            f"6. **International Helpline Directory**: https://findahelpline.com/"
        )


