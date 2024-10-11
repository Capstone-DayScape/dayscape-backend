from flask import Flask, request, jsonify
from openai import OpenAI
from google_secrets import get_secret

app = Flask(__name__)

# Dummy list of Places API types
places_api_types = [
    "accounting", "airport", "amusement_park", "aquarium", "art_gallery", "atm", "bakery", "bank", "bar", "beauty_salon", "bicycle_store", "book_store", "bowling_alley", "bus_station", "cafe", "campground", "car_dealer", "car_rental", "car_repair", "car_wash", "casino", "cemetery", "church", "city_hall", "clothing_store", "convenience_store", "courthouse", "dentist", "department_store", "doctor", "drugstore", "electrician", "electronics_store", "embassy", "fire_station", "florist", "funeral_home", "furniture_store", "gas_station", "gym", "hair_care", "hardware_store", "hindu_temple", "home_goods_store", "hospital", "insurance_agency", "jewelry_store", "laundry", "lawyer", "library", "light_rail_station", "liquor_store", "local_government_office", "locksmith", "lodging", "meal_delivery", "meal_takeaway", "mosque", "movie_rental", "movie_theater", "moving_company", "museum", "night_club", "painter", "park", "parking", "pet_store", "pharmacy", "physiotherapist", "plumber", "police", "post_office", "primary_school", "real_estate_agency", "restaurant", "roofing_contractor", "rv_park", "school", "secondary_school", "shoe_store", "shopping_mall", "spa", "stadium", "storage", "store", "subway_station", "supermarket", "synagogue", "taxi_stand", "tourist_attraction", "train_station", "transit_station", "travel_agency", "university", "veterinary_care", "zoo"
]

# Initialize OpenAI client
openai_api_key = get_secret("openai")
client = OpenAI(api_key=openai_api_key)

# Function to call the LLM API
def match_to_places_api_types(input_list):
    prompt = f"Match the following list of strings to the closest types from the Places API list: {places_api_types}. Return only the list of matched types, you should never have fewer output strings than three, and hopefully more options than you got inputs.\n\nInput list: {input_list}\n\nOutput list:"

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Use gpt-4o-mini model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100
    )

    # Extract the content and parse the list
    content = response.choices[0].message.content.strip()
    # Assuming the response is in the format "Output list: ['cafe', 'gym', 'library']"
    start = content.find("[")
    end = content.find("]") + 1
    matched_list = eval(content[start:end])
    return matched_list

@app.route('/match', methods=['POST'])
def match_strings():
    data = request.json
    input_list = data.get('input_list', [])
    matched_list = match_to_places_api_types(input_list)
    return jsonify({'matched_list': matched_list})

@app.route('/')
def hello_world():
    print("Hello, World! - Printed to console")
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)