import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ParsedLLMResponse:
    """Classe pour stocker la réponse parsée du LLM évaluateur"""
    navigation_graph: Dict[str, Any]
    verdict: str
    status: str  # 'SUCCESS', 'FAILURE', ou 'IMPOSSIBLE'
    guide: str
    raw_response: str


class LLMResponseParser:
    """Parser pour les réponses du LLM évaluateur"""
    
    def __init__(self):
        self.json_pattern = r'```json\s*(.*?)\s*```'
        self.verdict_pattern = r'<verdict>\s*(.*?)\s*</verdict>'
        self.guide_pattern = r'<guide>\s*(.*?)\s*</guide>'
    
    def parse(self, llm_response: str) -> ParsedLLMResponse:
        """
        Parse la réponse du LLM évaluateur
        
        Args:
            llm_response: La réponse brute du LLM
            
        Returns:
            ParsedLLMResponse: Objet contenant les éléments parsés
        """
        # Extraire le graph de navigation (JSON)
        navigation_graph = self._extract_navigation_graph(llm_response)
        
        # Extraire le verdict
        verdict = self._extract_verdict(llm_response)
        
        # Déterminer le status basé sur le verdict
        status = self._determine_status(verdict)
        
        # Extraire le guide
        guide = self._extract_guide(llm_response)
        
        return ParsedLLMResponse(
            navigation_graph=navigation_graph,
            verdict=verdict,
            status=status,
            guide=guide,
            raw_response=llm_response
        )
    
    def _extract_navigation_graph(self, response: str) -> Dict[str, Any]:
        """Extrait le graph de navigation depuis les balises ```json```"""
        match = re.search(self.json_pattern, response, re.DOTALL)
        if not match:
            raise ValueError("Aucun graph de navigation JSON trouvé dans la réponse")
        
        json_content = match.group(1).strip()
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de parsing JSON du graph de navigation: {e}")
    
    def _extract_verdict(self, response: str) -> str:
        """Extrait le verdict depuis les balises <verdict></verdict>"""
        match = re.search(self.verdict_pattern, response, re.DOTALL)
        if not match:
            raise ValueError("Aucun verdict trouvé dans la réponse")
        
        return match.group(1).strip()
    
    def _determine_status(self, verdict: str) -> str:
        """Détermine le status basé sur le contenu du verdict"""
        verdict_upper = verdict.upper()
        
        if 'SUCCESS' in verdict_upper:
            return 'SUCCESS'
        elif 'FAILURE' in verdict_upper:
            return 'FAILURE'
        elif 'IMPOSSIBLE' in verdict_upper:
            return 'IMPOSSIBLE'
        else:
            return 'UNKNOWN'
    
    def _extract_guide(self, response: str) -> str:
        """Extrait le guide depuis les balises <guide></guide>"""
        match = re.search(self.guide_pattern, response, re.DOTALL)
        if not match:
            return ""  # Le guide peut être optionnel
        
        return match.group(1).strip()


def parse_llm_evaluation_response(llm_response: str) -> ParsedLLMResponse:
    """
    Fonction utilitaire pour parser rapidement une réponse du LLM évaluateur
    
    Args:
        llm_response: La réponse brute du LLM
        
    Returns:
        ParsedLLMResponse: Objet contenant les éléments parsés
    """
    parser = LLMResponseParser()
    return parser.parse(llm_response)


# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple de test avec la réponse fournie
    example_response = '''
Let me analyze the navigation sequence and build a graph of the user's journey on Booking.com.

## Step 1: Identify visited pages
- Home Page: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
- Search Results Page: [15, 16, 17]
- Property Detail Page: [18, 19, 20, 21, 22, 23, 24]

## Step 2: Navigation Graph
```json
{
  "Home Page": {
    "url": "https://www.booking.com/",
    "layout": "Main booking search interface with search bar, property types, and popular destinations",
    "elements": [
      "I: Search bar 'Where are you going?' @top",
      "I: Date picker for check-in/check-out @top",
      "I: Guests selector (adults, children, rooms) @top",
      "C: Property type cards ['Hotels', 'Apartments', 'Resorts', 'Villas'] @center",
      "C: Popular destinations ['Paris', 'Marseille'] with images @bottom",
      "C: 'Sign in or register' button @top-right",
      "C: 'Save on stays' promotional button @center"
    ],
    "outgoing_links": [
      {
        "target": "Search Results Page",
        "action": "Enter destination, dates, guests and click Search"
      }
    ],
    "visited_steps": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
  },
  "Search Results Page": {
    "url": "https://www.booking.com/searchresults.html",
    "layout": "List of properties matching search criteria with filters",
    "elements": [
      "C: Property cards with images, names, and prices @center",
      "C: Filter options @left-sidebar",
      "C: 'See availability' buttons @right of each property",
      "I: Price range slider @left-sidebar",
      "C: Property type filters @left-sidebar"
    ],
    "outgoing_links": [
      {
        "target": "Property Detail Page",
        "action": "Click on a property card or 'See availability' button"
      }
    ],
    "visited_steps": [15, 16, 17]
  },
  "Property Detail Page": {
    "url": "https://www.booking.com/hotel/fr/beautiful-120-m2-apartment-with-eiffel-tower-view.html",
    "layout": "Detailed property information with booking options",
    "elements": [
      "C: Property images gallery @top",
      "I: Room selection dropdown @center",
      "C: 'I'll reserve' button @right",
      "C: FAQ section 'Travellers are asking' @bottom",
      "I: Number of rooms selector @right",
      "C: Room type options with prices and features @center"
    ],
    "outgoing_links": [],
    "visited_steps": [18, 19, 20, 21, 22, 23, 24]
  }
}
```

## Step 3: Analysis

### <verdict>
SUCCESS
The user successfully navigated from the home page to a specific property in Paris, selected dates and guest numbers, and reached the booking interface. They were able to:
1. Enter search criteria (Paris, dates, 2 adults + 2 children)
2. View search results
3. Select a specific property
4. Access the booking interface with room options
</verdict>

### <guide>
To book accommodation on Booking.com:

1. On the Home Page:
   - Enter your destination in the search bar
   - Select your check-in and check-out dates
   - Set number of guests and rooms
   - Click "Search"

2. On the Search Results Page:
   - Use filters on the left to narrow down options
   - Browse property cards
   - Click "See availability" on your chosen property

3. On the Property Detail Page:
   - Review property information and images
   - Select number of rooms needed
   - Choose room type from available options
   - Click "I'll reserve" to proceed with booking

Tips:
- Use filters to narrow down options matching your needs
- Check cancellation policies and included amenities
- Review property location and access information
- Compare room types and prices before selecting
</guide>
'''
    
    try:
        parsed_response = parse_llm_evaluation_response(example_response)
        print("Parsing réussi!")
        print(f"Status: {parsed_response.status}")
        print(f"Nombre de pages dans le graph: {len(parsed_response.navigation_graph)}")
        print(f"Verdict: {parsed_response.verdict[:100]}...")
        print(f"Guide: {parsed_response.guide[:100]}...")
    except Exception as e:
        print(f"Erreur lors du parsing: {e}") 