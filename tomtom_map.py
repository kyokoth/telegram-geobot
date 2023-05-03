import requests

class TomtomAPI:
    def __init__(self, key: str) -> None:
        self.key = key
        self.base_link = "https://api.tomtom.com/search/2/"
    
    def reverse_geocode(self, lat: float, lon: float):
        '''
        Converts the latitude and longitude into information about a place
        '''
        link = f"{self.base_link}reverseGeocode/{lat},{lon}.json?key={self.key}&radius=100"
        
        response = requests.get(link)
        
        return response.json()
    
    def nearby_search(self, lat: float, lon: float, lang: str, place: str):
        '''
        Finds nearby places based on latitude, longitude, language, and place type
        '''
        place_code = self._find_place_code(lang, place)
        
        if place_code == None:
            return None
        
        places_link = f"{self.base_link}nearbySearch/.json?key={self.key}&lat={lat}&lon={lon}&language={lang}&categorySet={place_code}"

        places_response = requests.get(places_link)
        
        return places_response.json()

    def _find_place_code(self, lang: str, place: str):
        '''
        Obtains a place code based on place type and language
        '''
        categories_link = f"{self.base_link}poiCategories.json?key={self.key}&language={lang}"

        categories_response = requests.get(categories_link)

        for category in categories_response.json()["poiCategories"]:
            if category['name'] == place or place in category['synonyms']:
                return category['id']
        return None
