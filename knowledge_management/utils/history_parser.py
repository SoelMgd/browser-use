import json
import base64
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_history_from_file(file_path: str) -> Dict[str, Any]:
    """
    Charge l'historique depuis un fichier JSON
    
    Args:
        file_path: Chemin vers le fichier JSON d'historique
        
    Returns:
        Dictionnaire contenant l'historique
    """
    logger.info(f"Loading history from file: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    logger.info(f"Successfully loaded history with {len(data.get('history', []))} steps")
    return data


def history_to_messages(history_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract and parses history to a list of text messages and associated images to create graphs
    
    Args:
        history_data: Loaded history
        
    Returns:
        List of dict, each one containing the message explaining the step and the associated screenshot.
    """
    logger.info("Starting history_to_messages parsing")
    
    # TODO maybe we could keep only done actions in the future
    steps = []
    
    history_list = history_data.get('history', [])
    logger.info(f"Found {len(history_list)} steps in history")
    
    for i, step in enumerate(history_list):
        logger.debug(f"Processing step {i}")
        step_dict = {}
        
        # Extract actions to create the text message
        model_output = step.get('model_output', {})
        action_strings = []
        
        # Collect actions
        if model_output and 'action' in model_output:
            logger.debug(f"Step {i}: Found {len(model_output['action'])} actions")
            for action in model_output['action']:
                action_detailed = get_detailed_action_decription(action)
                action_strings.append(action_detailed)
                action_name = list(action.keys())[0]
                logger.debug(f"Step {i}: Action found: {action_name}")
        else:
            logger.debug(f"Step {i}: No actions found")
                
        # Join actions in a single message
        actions_str = f"This is step {i}, "

        url = step.get('state', {}).get('url', '')
        if url:
            truncated_url = url[:120]+'...' if len(url) >120 else url
            actions_str += f'the screenshot has been taken at this url {truncated_url}. '
            logger.debug(f"Step {i}: URL found: {truncated_url}")
        
        if len(action_strings) == 1:
            actions_str += str(action_strings[0])
        elif len(action_strings) > 1:
            for j, action in enumerate(action_strings):
                actions_str += f'The {j}th action taken for step {i} is ' + str(action_strings[j])
        else:
            actions_str += "No actions found for this step"

        step_dict['actions'] = actions_str
        step_dict['screenshot'] = step.get('state', {}).get('screenshot', '')
        
        logger.debug(f"Step {i}: Created message: {actions_str[:100]}...")
        steps.append(step_dict)
    
    logger.info(f"Successfully processed {len(steps)} steps")
    return steps


def get_detailed_action_decription(action):
    """
    Return action description with additional details for some specifc actions."""

    # Get the action name (first key in the dictionary)
    action_name = list(action.keys())[0]
    action_params = action[action_name]

    if action_name == 'click_element_by_index':
        element_id = str(action_params.get('index', 'unknown'))
        return f'The user clicked on element {element_id}.'
    elif action_name == 'get_dropdown_options':
        element_id = str(action_params.get('index', 'unknown'))
        return f'The user clicked on dropdown option {element_id}.'
    elif action_name == 'select_dropdown_option':
        text = str(action_params.get('text', ''))
        if text:
            return f'The user clicked on dropdown option {text}.'
        element_id = str(action_params.get('index', 'unknown'))
        return f'The user clicked on dropdown option {element_id}.'
    elif action_name == 'input_text':
        element_id = str(action_params.get('index', 'unknown'))
        text = action_params.get('text', 'unknown text')
        return f"The user typed: '{text}' in element {element_id}."
    elif action_name == 'scroll_down':
        amount = str(action_params.get('amount', 'unknown'))
        return f"The user scrolled down for {amount} pixels."
    elif action_name == 'scroll_up':
        amount = str(action_params.get('amount', 'unknown'))
        return f"The user scrolled up for {amount} pixels."
    elif action_name == 'switch_tab':
        page_id = str(action_params.get('page_id', 'unknown'))
        return f"The user switched to tab {page_id}."
    elif action_name == 'go_to_url':
        url = action_params.get('url', 'unknown url')
        return f"The user navigated to: {url}"
    elif action_name == 'write_file':
        file_name = action_params.get('file_name', 'unknown file')
        return f"The user wrote to file: {file_name}"
    elif action_name == 'search_google':
        query = action_params.get('query', 'unknown query')
        return f"The user searched Google for: '{query}'"
    elif action_name == 'wait':
        seconds = str(action_params.get('seconds', 'unknown'))
        return f"The user waited for {seconds} seconds."
    elif action_name == 'done':
        success = action_params.get('success', 'unknown')
        text = action_params.get('text', 'no text')
        return f"The user stopped the tasks" # no need to detail
    else:
        return f"The user performed action: {action_name}"



def save_screenshot_to_file(screenshot_base64: str, output_path: str) -> bool:
    """
    Sauvegarde un screenshot base64 vers un fichier image
    
    Args:
        screenshot_base64: Données base64 du screenshot
        output_path: Chemin de sortie pour l'image
        
    Returns:
        True si sauvegarde réussie, False sinon
    """
    try:
        # Décoder les données base64
        image_data = base64.b64decode(screenshot_base64)
        
        # Créer le dossier parent si nécessaire
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder l'image
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde du screenshot: {e}")
        return False


def save_all_screenshots(history_data: Dict[str, Any], output_dir: str) -> List[str]:
    """
    Sauvegarde tous les screenshots de l'historique
    
    Args:
        history_data: Données de l'historique
        output_dir: Dossier de sortie pour les images
        
    Returns:
        Liste des chemins des fichiers sauvegardés
    """
    logger.info("Starting to save all screenshots")
    screenshots = []
    
    for i, step in enumerate(history_data.get('history', [])):
        screenshot = step.get('state', {}).get('screenshot', '')
        if screenshot:
            screenshots.append({
                'step_number': i,
                'screenshot_base64': screenshot
            })
    
    saved_files = []
    
    for screenshot in screenshots:
        step_number = screenshot['step_number']
        filename = f"step_{step_number}.png"
        output_path = Path(output_dir) / filename
        
        if save_screenshot_to_file(screenshot['screenshot_base64'], str(output_path)):
            saved_files.append(str(output_path))
    
    logger.info(f"Saved {len(saved_files)} screenshots")
    return saved_files


if __name__ == '__main__':
    # Example
    history_file = '/Users/twin/Documents/Browser-Use-Graph/browser-use/tmp/history.json'
    
    try:
        logger.info("Starting history parser")
        
        # Load history data first
        history_data = load_history_from_file(history_file)
        
        # Parse history to messages
        parsed_data = history_to_messages(history_data)
        
        # Print text messages for each steps
        logger.info("Printing messages for each step:")
        for i, step in enumerate(parsed_data):
            print(step['actions'])
            print(f"Screenshot available: {'Yes' if step['screenshot'] else 'No'}")
            print()

        # Example: save screenshots
        output_dir = './screenshots'
        saved_files = save_all_screenshots(history_data, output_dir)
        print(f"\n💾 Screenshots sauvegardés: {len(saved_files)} fichiers")
        
    except FileNotFoundError:
        logger.error(f"❌ File not found: {history_file}")
    except Exception as e:
        logger.error(f"❌ Parsing error: {e}", exc_info=True) 