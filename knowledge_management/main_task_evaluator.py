"""
Script principal pour l'exécution et l'évaluation de tâches avec Browser-Use.

Ce script :
1. Exécute une tâche avec Browser-Use
2. Évalue le résultat avec un LLM évaluateur
3. En cas d'échec, réessaie avec le guide généré par l'évaluateur
4. Sauvegarde les graphs de navigation et les plans de succès
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

# Imports Browser-Use
from browser_use.agent.service import Agent
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.llm import ChatAnthropic

# Imports locaux
from knowledge_management.utils.history_parser import load_history_from_file, history_to_llm_messages, save_all_screenshots
from knowledge_management.utils.llm_response_parser import parse_llm_evaluation_response, ParsedLLMResponse
from knowledge_management.prompts.graph_generation_prompts import SYSTEM_PROMPT_GRAPH_GENERATION

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()


class TaskEvaluator:
    """Classe principale pour l'évaluation et l'amélioration de tâches"""
    
    def __init__(self, max_attempts: int = 3):
        self.max_attempts = max_attempts
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY non définie dans les variables d'environnement")
        
        # Initialiser Browser-Use
        self.browser_session = BrowserSession(
            browser_profile=BrowserProfile(
                headless=False,  # True en production
                minimum_wait_page_load_time=3,
                maximum_wait_page_load_time=10,
                viewport={'width': 1280, 'height': 1100},
                user_data_dir='~/.config/browseruse/profiles/default',
            )
        )
        
        # Initialiser le LLM pour Browser-Use
        self.browser_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
        )
        
        # Initialiser le LLM évaluateur
        self.evaluator_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=self.api_key,
            max_tokens=6000,
            temperature=0.1
        )
        
        # Chemins de sauvegarde
        self.navigation_graphs_dir = Path(__file__).parent / "navigation_graphs"
        self.plans_dir = Path(__file__).parent / "plans"
        self.screenshots_dir = Path(__file__).parent / "screenshots"
        self.tmp_dir = Path(__file__).parent.parent.parent / "tmp"
        
        # Créer les dossiers si nécessaire
        self.navigation_graphs_dir.mkdir(exist_ok=True)
        self.plans_dir.mkdir(exist_ok=True)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.tmp_dir.mkdir(exist_ok=True)
    
    def _generate_task_id(self, task: str) -> str:
        """Génère un ID unique pour la tâche"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_hash = hash(task) % 10000
        return f"task_{timestamp}_{task_hash}"
    
    def _save_navigation_graph(self, task_id: str, attempt: int, navigation_graph: dict):
        """Sauvegarde le graph de navigation"""
        filename = f"{task_id}_attempt_{attempt}_graph.json"
        filepath = self.navigation_graphs_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(navigation_graph, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Graph de navigation sauvegardé : {filepath}")
    
    def _save_successful_plan(self, task_id: str, guide: str):
        """Sauvegarde le plan de succès"""
        filename = f"{task_id}_successful_plan.txt"
        filepath = self.plans_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(guide)
        
        logger.info(f"✅ Plan de succès sauvegardé : {filepath}")
    
    def _build_system_prompt_with_guide(self, guide: str) -> str:
        """Construit un contexte de message enrichi avec le guide"""
        enhanced_context = f"""## A precedent user already tried this task before and let some recommendations that might be helpful.

{guide}

Use this guide to improve your approach."""
        return enhanced_context
    
    async def _evaluate_task_execution(self, history_file: str, task: str) -> ParsedLLMResponse:
        """Évalue l'exécution d'une tâche avec le LLM évaluateur"""
        try:
            # Charger l'historique
            history_data = load_history_from_file(history_file)
            
            # Convertir en messages LLM
            llm_messages = history_to_llm_messages(history_data)
            
            # Créer le message système avec la task
            from browser_use.llm.messages import SystemMessage
            enhanced_system_prompt = f"""{SYSTEM_PROMPT_GRAPH_GENERATION}

## The user try to reach this goal:
{task}

Please evaluate the user trajectory for this goal."""
            system_message = SystemMessage(content=enhanced_system_prompt)
            
            # Préparer tous les messages
            all_messages = [system_message] + llm_messages
            
            # Envoyer au LLM évaluateur
            logger.info("🔍 Évaluation en cours...")
            response = await self.evaluator_llm.ainvoke(all_messages)
            
            # Parser la réponse
            parsed_response = parse_llm_evaluation_response(response.completion)
            
            logger.info(f"📋 Évaluation terminée - Status: {parsed_response.status}")
            return parsed_response
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'évaluation : {e}")
            raise
    
    async def _execute_task(self, task: str, enhanced_prompt: Optional[str] = None) -> str:
        """Exécute une tâche avec Browser-Use"""
        try:
            # Créer l'agent avec le contexte de message personnalisé si fourni
            agent_kwargs = {
                'task': task,
                'llm': self.browser_llm,
                'browser_session': self.browser_session,
                'validate_output': True,
                'enable_memory': False,
            }
            
            if enhanced_prompt:
                agent_kwargs['message_context'] = enhanced_prompt
            
            agent = Agent(**agent_kwargs)
            
            # Exécuter la tâche
            logger.info("🚀 Exécution de la tâche...")
            history = await agent.run(max_steps=25)
            
            # Sauvegarder l'historique
            history_file = self.tmp_dir / "history.json"
            history.save_to_file(str(history_file))
            
            return str(history_file)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution de la tâche : {e}")
            raise
    
    async def run_task_with_evaluation(self, task: str) -> dict:
        """
        Exécute une tâche avec évaluation et amélioration itérative
        
        Args:
            task: La tâche à exécuter
            
        Returns:
            dict: Résultats de l'exécution
        """
        task_id = self._generate_task_id(task)
        logger.info(f"🎯 Début de l'exécution de la tâche : {task_id}")
        logger.info(f"📝 Tâche : {task}")
        
        results = {
            'task_id': task_id,
            'task': task,
            'attempts': [],
            'final_status': None,
            'successful_plan': None
        }
        
        current_guide = None
        
        for attempt in range(1, self.max_attempts + 1):
            logger.info(f"\n🔄 Tentative {attempt}/{self.max_attempts}")
            
            try:
                # Construire le contexte de message enrichi si on a un guide
                message_context = None
                if current_guide:
                    message_context = self._build_system_prompt_with_guide(current_guide)
                
                # Exécuter la tâche
                history_file = await self._execute_task(task, message_context)
                
                # Évaluer le résultat
                evaluation = await self._evaluate_task_execution(history_file, task)
                
                # Sauvegarder le graph de navigation
                self._save_navigation_graph(task_id, attempt, evaluation.navigation_graph)
                
                # Sauvegarder les screenshots
                screenshots = self._save_screenshots(task_id, attempt, history_file)
                
                # Enregistrer les résultats de cette tentative
                attempt_result = {
                    'attempt_number': attempt,
                    'status': evaluation.status,
                    'verdict': evaluation.verdict,
                    'guide': evaluation.guide,
                    'navigation_graph_file': f"{task_id}_attempt_{attempt}_graph.json",
                    'screenshots': screenshots
                }
                results['attempts'].append(attempt_result)
                
                logger.info(f"📊 Tentative {attempt} - Status: {evaluation.status}")
                
                # Si succès, sauvegarder le plan et terminer
                if evaluation.status == 'SUCCESS':
                    logger.info("✅ Tâche accomplie avec succès!")
                    self._save_successful_plan(task_id, evaluation.guide)
                    results['final_status'] = 'SUCCESS'
                    results['successful_plan'] = evaluation.guide
                    break
                
                # Si échec, utiliser le guide pour la prochaine tentative
                elif evaluation.status == 'FAILURE':
                    current_guide = evaluation.guide
                    logger.info("⚠️ Échec détecté, utilisation du guide pour la prochaine tentative")
                    
                # Si impossible, arrêter
                elif evaluation.status == 'IMPOSSIBLE':
                    logger.info("❌ Tâche impossible à accomplir")
                    results['final_status'] = 'IMPOSSIBLE'
                    break
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la tentative {attempt} : {e}")
                attempt_result = {
                    'attempt_number': attempt,
                    'status': 'ERROR',
                    'error': str(e)
                }
                results['attempts'].append(attempt_result)
        
        # Si toutes les tentatives ont échoué
        if not results['final_status']:
            results['final_status'] = 'FAILURE_AFTER_MAX_ATTEMPTS'
            logger.warning("⚠️ Échec après le nombre maximum de tentatives")
        
        return results

    def _save_screenshots(self, task_id: str, attempt: int, history_file: str):
        """Sauvegarde les screenshots de la tentative"""
        try:
            # Charger l'historique
            history_data = load_history_from_file(history_file)
            
            # Créer le dossier pour cette tentative
            screenshots_dir = self.screenshots_dir / f"{task_id}_attempt_{attempt}"
            screenshots_dir.mkdir(exist_ok=True)
            
            # Sauvegarder tous les screenshots
            saved_files = save_all_screenshots(history_data, str(screenshots_dir))
            
            logger.info(f"📸 Screenshots sauvegardés : {len(saved_files)} images dans {screenshots_dir}")
            return saved_files
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la sauvegarde des screenshots : {e}")
            return []


async def main():
    """Fonction principale"""

    CREDENTIALS = """ To login, use the following credentials: {
  username: 'soel@twin.so',
  password: 'Agent123456!',
}"""
    # Configuration
    TASK = """
    "Log in to your Airbnb account, save a Guest Favorite property to your wishlist, and then go to your wishlist and remove the property you previously added.
    Only use http://airbnb.com to achieve the task. Don't go to any other site. The task is achievable with just navigation from this site."
    """

    TASK = TASK + CREDENTIALS
    
    try:
        # Créer l'évaluateur
        evaluator = TaskEvaluator(max_attempts=3)
        
        # Exécuter la tâche avec évaluation
        results = await evaluator.run_task_with_evaluation(TASK)
        
        # Afficher les résultats finaux
        print("\n" + "="*80)
        print("🎯 RÉSULTATS FINAUX")
        print("="*80)
        print(f"Task ID: {results['task_id']}")
        print(f"Status final: {results['final_status']}")
        print(f"Nombre de tentatives: {len(results['attempts'])}")
        
        if results['successful_plan']:
            print(f"\n📋 Plan de succès sauvegardé dans: {evaluator.plans_dir}")
        
        print(f"\n📊 Graphs de navigation sauvegardés dans: {evaluator.navigation_graphs_dir}")
        print(f"📸 Screenshots sauvegardés dans: {evaluator.screenshots_dir}")
        
        # Afficher le détail des tentatives
        print(f"\n📝 Détail des tentatives:")
        for attempt in results['attempts']:
            print(f"  Tentative {attempt['attempt_number']}: {attempt['status']}")
            if 'verdict' in attempt:
                print(f"    Verdict: {attempt['verdict'][:100]}...")
            if 'screenshots' in attempt and attempt['screenshots']:
                print(f"    Screenshots: {len(attempt['screenshots'])} images sauvegardées")
        
    except Exception as e:
        logger.error(f"❌ Erreur dans main : {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main()) 