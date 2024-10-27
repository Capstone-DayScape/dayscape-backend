from pydantic import BaseModel
from openai import OpenAI
from google_secrets import get_secret

# List of Places API types https://developers.google.com/maps/documentation/places/web-service/supported_types
places_api_types = ["accounting", "airport", "amusement_park",
                    "aquarium", "art_gallery", "atm", "bakery", "bank", "bar",
                    "beauty_salon", "bicycle_store", "book_store", "bowling_alley",
                    "bus_station", "cafe", "campground", "car_dealer", "car_rental",
                    "car_repair", "car_wash", "casino", "cemetery", "church",
                    "city_hall", "clothing_store", "convenience_store", "courthouse",
                    "dentist", "department_store", "doctor", "drugstore",
                    "electrician", "electronics_store", "embassy", "fire_station",
                    "florist", "funeral_home", "furniture_store", "gas_station",
                    "gym", "hair_care", "hardware_store", "hindu_temple",
                    "home_goods_store", "hospital", "insurance_agency",
                    "jewelry_store", "laundry", "lawyer", "library",
                    "light_rail_station", "liquor_store", "local_government_office",
                    "locksmith", "lodging", "meal_delivery", "meal_takeaway",
                    "mosque", "movie_rental", "movie_theater", "moving_company",
                    "museum", "night_club", "painter", "park", "parking", "pet_store",
                    "pharmacy", "physiotherapist", "plumber", "police", "post_office",
                    "primary_school", "real_estate_agency", "restaurant",
                    "roofing_contractor", "rv_park", "school", "secondary_school",
                    "shoe_store", "shopping_mall", "spa", "stadium", "storage",
                    "store", "subway_station", "supermarket", "synagogue",
                    "taxi_stand", "tourist_attraction", "train_station",
                    "transit_station", "travel_agency", "university",
                    "veterinary_care", "zoo"]

# Initialize OpenAI client
openai_api_key = get_secret("openai")
client = OpenAI(api_key=openai_api_key)


class GooglePlacesTypeList(BaseModel):
    types: list[str]


# Function to call the LLM API
def match_to_places_api_types(input_list):
    response = client.beta.chat.completions.parse(
        model="gpt-4o-mini",  # Use gpt-4o-mini model
        messages=[
            {"role": "system", "content":
            f"Convert the input words or phrases into a list of all related Google Places \"types\" at a ratio of 1 input to 1 Google Place \"type\". Here are the valid \"types\": {places_api_types}"},
            {"role": "user", "content": f"Input list: {input_list}"}
        ],
        response_format=GooglePlacesTypeList,
    )

    return response.choices[0].message.parsed
