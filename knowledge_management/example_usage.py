"""
Exemple d'utilisation du système de knowledge management avec choix du fournisseur LLM.

Ce script montre comment utiliser TaskEvaluator, NavigationGraphManager et GuideGenerator
avec différents fournisseurs LLM (Anthropic ou OpenAI).
"""

import asyncio
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des classes
from main_task_evaluator import TaskEvaluator
from utils.navigation_graph_manager import NavigationGraphManager
from utils.guide_generator import GuideGenerator


async def example_with_anthropic():
    """Exemple d'utilisation avec Anthropic (par défaut)"""
    logger.info("🚀 Exemple avec Anthropic")
    
    try:
        # Initialiser TaskEvaluator avec Anthropic (par défaut)
        evaluator = TaskEvaluator(max_attempts=2, llm_provider="anthropic")
        
        # Exemple de tâche
        task = "Rechercher un hôtel à Paris sur Booking.com"
        website_url = "https://www.booking.com"
        
        logger.info(f"📝 Tâche: {task}")
        logger.info(f"🌐 Site: {website_url}")
        
        # Exécuter la tâche (commenté pour éviter l'exécution réelle)
        # results = await evaluator.run_task_with_evaluation(task, website_url)
        # logger.info(f"✅ Résultats: {results}")
        
    except Exception as e:
        logger.error(f"❌ Erreur avec Anthropic: {e}")


async def example_with_openai():
    """Exemple d'utilisation avec OpenAI"""
    logger.info("🚀 Exemple avec OpenAI")
    
    try:
        # Initialiser TaskEvaluator avec OpenAI
        evaluator = TaskEvaluator(max_attempts=2, llm_provider="openai")
        
        # Exemple de tâche
        task = "Rechercher un vol vers Tokyo sur Expedia"
        website_url = "https://www.expedia.com"
        
        logger.info(f"📝 Tâche: {task}")
        logger.info(f"🌐 Site: {website_url}")
        
        # Exécuter la tâche (commenté pour éviter l'exécution réelle)
        # results = await evaluator.run_task_with_evaluation(task, website_url)
        # logger.info(f"✅ Résultats: {results}")
        
    except Exception as e:
        logger.error(f"❌ Erreur avec OpenAI: {e}")


async def example_individual_components():
    """Exemple d'utilisation des composants individuels"""
    logger.info("🚀 Exemple des composants individuels")
    
    try:
        # NavigationGraphManager avec OpenAI
        nav_manager = NavigationGraphManager(llm_provider="openai")
        logger.info("✅ NavigationGraphManager initialisé avec OpenAI")
        
        # GuideGenerator avec Anthropic
        guide_generator = GuideGenerator(llm_provider="anthropic")
        logger.info("✅ GuideGenerator initialisé avec Anthropic")
        
        # Exemple de génération de guide
        task = "Se connecter à Gmail"
        website_url = "https://gmail.com"
        
        guide = await guide_generator.generate_optimized_guide(
            task=task,
            website_url=website_url,
            rag_plans_context="Contexte des plans RAG...",
            navigation_graph_context="Contexte du graph de navigation...",
            previous_guide_context="Guide précédent...",
            attempt_count=1
        )
        
        logger.info(f"📋 Guide généré: {guide[:100]}...")
        
    except Exception as e:
        logger.error(f"❌ Erreur avec les composants individuels: {e}")


async def main():
    """Fonction principale"""
    logger.info("🎯 Démonstration du système de knowledge management")
    
    # Exemple avec Anthropic
    await example_with_anthropic()
    
    print("\n" + "="*50 + "\n")
    
    # Exemple avec OpenAI
    await example_with_openai()
    
    print("\n" + "="*50 + "\n")
    
    # Exemple des composants individuels
    await example_individual_components()
    
    logger.info("✅ Démonstration terminée")


if __name__ == "__main__":
    asyncio.run(main()) 