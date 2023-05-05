import requests

class TomtomAPI:
    def __init__(self, key_tomtom: str, key_geoapify: str) -> None:
        self.key_tomtom = key_tomtom
        self.key_geoapify = key_geoapify
        self.base_link_tomtom = "https://api.tomtom.com/search/2/"
        self.base_link_geoapify = "https://api.geoapify.com/v2/"
    
    def reverse_geocode(self, lat: str, lon: str):
        '''
        Converts the latitude and longitude into information about a place
        '''
        link = f"{self.base_link_tomtom}reverseGeocode/{lat},{lon}.json?key={self.key_tomtom}"
        
        response = requests.get(link)
        
        return response.json()
    
    def nearby_search(self, lat: str, lon: str, lang: str, query: str):
        '''
        Finds nearby places based on latitude, longitude, language, and place type
        '''
        place_code = self._find_place_code(lang, query.capitalize())
        
        if place_code == None:
            return None
        
        places_link = f"{self.base_link_tomtom}nearbySearch/.json?key={self.key_tomtom}&lat={lat}&lon={lon}&language={lang}&categorySet={place_code}"

        places_response = requests.get(places_link)
        
        return places_response.json()

    def place_details(self, lat: str, lon: str, lang: str):
        place_link = f"{self.base_link_geoapify}place-details?lat={lat}&lon={lon}&lang={lang}&apiKey={self.key_geoapify}"

        place_response = requests.get(place_link)

        return place_response.json()

    def place_by_id(self,
                    entityId: str,
                    language: str = 'en-US',
                    openingHours: str = 'nextSevenDays',
                    timeZone: str = 'iana',
                    mapcodes: str = 'Local,Alternative,International',
                    relatedPois: str = 'off',
                    view: str = 'Unified') -> list:
        
        link = f"{self.base_link_tomtom}place.json"

        response = requests.get(link, params={
            "entityId": entityId,
            "key": self.key_tomtom,
            "language": language,
            "openingHours": openingHours,
            "timeZone": timeZone,
            "mapcodes": mapcodes,
            "relatedPois": relatedPois,
            "view": view
        })

        return response.json()



    def _find_place_code(self, lang: str, query: str):
        '''
        Obtains a place code based on place type and language
        '''
        categories_link = f"{self.base_link_tomtom}poiCategories.json?key={self.key_tomtom}&language={lang}"

        categories_response = requests.get(categories_link)

        for category in categories_response.json()['poiCategories']:
            if category['name'] == query or query in category['synonyms']:
                return category['id']
        return None
