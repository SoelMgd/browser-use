import json
import re
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParsedLLMResponse:
    """Classe pour stocker la réponse parsée du LLM évaluateur"""
    navigation_graph: Dict[str, Any]
    verdict: str
    guide: Dict[str, Any]
    failure_guide: str
    raw_response: str
    task_label: str  # First element of the tuple (SUCCESS, FAILURE, IMPOSSIBLE)
    website_url: str  # Second element of the tuple (main URL)
    task_title: str  # Third element of the tuple (generalized title)


class LLMResponseParser:
    """Parser pour les réponses du LLM évaluateur"""
    
    def __init__(self):
        self.json_pattern = r'```json\s*(.*?)\s*```'
        self.verdict_pattern = r'<verdict>\s*(.*?)\s*</verdict>'
        self.guide_pattern = r'<guide>\s*(.*?)\s*</guide>'
        self.failure_guide_pattern = r'<failure_guide>\s*(.*?)\s*</failure_guide>'
        self.tuple_pattern = r'\([\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"],\s*[\'"]([^\'"]+)[\'"]\)'
    
    def parse(self, llm_response: str) -> ParsedLLMResponse:
        """
        Parse la réponse du LLM évaluateur
        
        Args:
            llm_response: La réponse brute du LLM
            
        Returns:
            ParsedLLMResponse: Objet contenant les éléments parsés
        """
        # Extraire le graph de navigation (JSON avant le verdict)
        navigation_graph = self._extract_navigation_graph(llm_response)
        
        # Extraire le verdict
        verdict = self._extract_verdict(llm_response)
        
        # Extraire le tuple du verdict
        task_label, website_url, task_title = self._extract_tuple_from_verdict(verdict)
        
        # Extraire le guide (JSON après le verdict)
        guide = self._extract_guide(llm_response)
        
        # Extraire le failure_guide (optionnel)
        failure_guide = self._extract_failure_guide(llm_response)
        
        return ParsedLLMResponse(
            navigation_graph=navigation_graph,
            verdict=verdict,
            guide=guide,
            failure_guide=failure_guide,
            raw_response=llm_response,
            task_label=task_label,
            website_url=website_url,
            task_title=task_title
        )
    
    def _extract_navigation_graph(self, response: str) -> Dict[str, Any]:
        """Extrait le graph de navigation depuis le premier bloc ```json``` (avant le verdict)"""
        # Trouver tous les blocs JSON
        json_matches = list(re.finditer(self.json_pattern, response, re.DOTALL))
        
        if not json_matches:
            raise ValueError("Aucun graph de navigation JSON trouvé dans la réponse")
        
        # Prendre le premier bloc JSON (avant le verdict)
        first_json_match = json_matches[0]
        json_content = first_json_match.group(1).strip()
        
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
    
    def _extract_tuple_from_verdict(self, verdict: str) -> Tuple[str, str, str]:
        """Extrait le tuple (LABEL, url, title) du verdict"""
        match = re.search(self.tuple_pattern, verdict)
        if not match:
            # Fallback: try to extract with different quote styles
            fallback_pattern = r'\(([^,]+),\s*([^,]+),\s*([^)]+)\)'
            match = re.search(fallback_pattern, verdict)
            if not match:
                raise ValueError("Aucun tuple trouvé dans le verdict")
            
            # Clean up the extracted values
            task_label = match.group(1).strip().strip("'\"")
            website_url = match.group(2).strip().strip("'\"")
            task_title = match.group(3).strip().strip("'\"")
        else:
            task_label = match.group(1)
            website_url = match.group(2)
            task_title = match.group(3)
        
        return task_label, website_url, task_title
    
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
    
    def _extract_guide(self, response: str) -> Dict[str, Any]:
        """Extrait le guide depuis le deuxième bloc ```json``` (après le verdict)"""
        # Trouver tous les blocs JSON
        json_matches = list(re.finditer(self.json_pattern, response, re.DOTALL))
        
        if len(json_matches) < 2:
            # Si il n'y a qu'un seul JSON ou aucun, retourner un dictionnaire vide
            return {}
        
        # Prendre le deuxième bloc JSON (après le verdict)
        second_json_match = json_matches[1]
        json_content = second_json_match.group(1).strip()
        
        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            # En cas d'erreur de parsing, retourner un dictionnaire vide
            print(f"Warning: Erreur de parsing JSON du guide: {e}")
            return {}
    
    def _extract_failure_guide(self, response: str) -> str:
        """Extrait le failure_guide depuis les balises <failure_guide></failure_guide>"""
        match = re.search(self.failure_guide_pattern, response, re.DOTALL)
        if not match:
            return ""  # Le failure_guide peut être optionnel
        
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

('SUCCESS', 'https://www.booking.com/', 'Book accommodation on Booking.com')
</verdict>

### Reusable lessons
</guide>

```json
{  
  "Booking.com: filter search results by air conditioning": "On the search results page, scroll the left sidebar until you see the 'Facilities' section, then tick the checkbox for 'Air conditioning' (AC).",  
  "Amazon: download an invoice": "On the 'Your Orders' page: from the top-right account menu, locate the order, click 'Invoice' or the download icon near the order summary."
}
```
'''
    
    try:
        parsed_response = parse_llm_evaluation_response(example_response)
        print("Parsing réussi!")
        print(f"Task Label: {parsed_response.task_label}")
        print(f"Website URL: {parsed_response.website_url}")
        print(f"Task Title: {parsed_response.task_title}")
        print(f"Nombre de pages dans le graph: {len(parsed_response.navigation_graph)}")
        print(f"Verdict: {parsed_response.verdict[:100]}...")
        print(f"Guide (type): {type(parsed_response.guide)}")
        print(f"Guide (contenu): {parsed_response.guide}")
        print(f"Failure Guide: {parsed_response.failure_guide}")
    except Exception as e:
        print(f"Erreur lors du parsing: {e}") 