"""
Générateur de guide optimisé basé sur les connaissances accumulées.

Ce module combine :
1. Plans RAG pour les tâches similaires
2. Graphs de navigation pour comprendre la structure du site
3. Guides des tentatives précédentes
4. Génération d'un guide optimisé via LLM
"""

import logging
from typing import List, Dict, Any, Optional

from browser_use.llm import ChatAnthropic
from browser_use.llm.messages import SystemMessage, UserMessage

from .plan_rag_manager import PlanRAGManager
from .navigation_graph_manager import NavigationGraphManager
from ..prompts.guide_generation_prompts import GUIDE_GENERATION_SYSTEM_PROMPT, GUIDE_GENERATION_USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class GuideGenerator:
    """Générateur de guide optimisé"""
    
    def __init__(self, api_key: str):
        """
        Initialise le générateur de guide
        
        Args:
            api_key: Clé API pour le LLM
        """
        self.api_key = api_key
        
        # Initialiser le LLM pour la génération de guide
        self.guide_llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=self.api_key,
            max_tokens=4000,
            temperature=0.2
        )
        
        # Initialiser les gestionnaires
        self.rag_manager = PlanRAGManager()
        self.nav_manager = NavigationGraphManager()
        
        logger.info("🎯 Guide Generator initialisé")
    
    async def generate_optimized_guide(
        self,
        task: str,
        website_url: str,
        task_title: Optional[str] = None,
        previous_guide: Optional[str] = None,
        attempt_count: int = 0
    ) -> str:
        """
        Génère un guide optimisé pour une tâche donnée
        
        Args:
            task: La tâche à exécuter
            website_url: URL du site web
            task_title: Titre de la tâche (pour la recherche RAG)
            previous_guide: Guide de la tentative précédente
            attempt_count: Nombre de tentatives précédentes
            
        Returns:
            Guide optimisé généré
        """
        try:
            logger.info("🔍 Génération de guide optimisé...")
            
            # 1. Récupérer les plans RAG similaires
            rag_plans_context = self._get_rag_plans_context(task_title, website_url)
            
            # 2. Récupérer les graphs de navigation
            nav_context = self._get_navigation_context(website_url)
            
            # 3. Préparer le contexte du guide précédent
            previous_guide_context = self._format_previous_guide(previous_guide)
            
            # 4. Déterminer le type de tâche
            task_type = self._determine_task_type(task)
            
            # 5. Générer le guide optimisé
            optimized_guide = await self._generate_guide_with_llm(
                task=task,
                rag_plans_context=rag_plans_context,
                navigation_graph_context=nav_context,
                previous_guide_context=previous_guide_context,
                website_url=website_url,
                task_type=task_type,
                attempt_count=attempt_count
            )
            
            logger.info("✅ Guide optimisé généré avec succès")
            return optimized_guide
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération du guide: {e}")
            # Retourner un guide de fallback
            return self._generate_fallback_guide(task, previous_guide)
    
    def _get_rag_plans_context(self, task_title: Optional[str], website_url: str) -> str:
        """Récupère le contexte des plans RAG"""
        if not task_title:
            return "No task title available for RAG search."
        
        try:
            similar_plans = self.rag_manager.find_similar_plans(task_title, website_url, top_k=3)
            if similar_plans:
                return self.rag_manager.build_context_from_similar_plans(similar_plans)
            else:
                return "No similar successful plans found in RAG database."
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la récupération des plans RAG: {e}")
            return "Error retrieving RAG plans."
    
    def _get_navigation_context(self, website_url: str) -> str:
        """Récupère le contexte des graphs de navigation"""
        try:
            graphs = self.nav_manager.find_navigation_graphs_for_website(website_url, max_age_days=30)
            if graphs:
                return self.nav_manager.build_navigation_context(graphs, max_graphs=3)
            else:
                return "No previous navigation patterns available for this website."
        except Exception as e:
            logger.warning(f"⚠️ Erreur lors de la récupération des graphs de navigation: {e}")
            return "Error retrieving navigation patterns."
    
    def _format_previous_guide(self, previous_guide: Optional[str]) -> str:
        """Formate le guide précédent"""
        if not previous_guide:
            return "No previous attempt guide available."
        
        return f"""Previous attempt guide:
{previous_guide}

Use this guide to understand what was tried before and avoid repeating unsuccessful approaches."""
    
    def _determine_task_type(self, task: str) -> str:
        """Détermine le type de tâche basé sur le contenu"""
        task_lower = task.lower()
        
        if any(word in task_lower for word in ['login', 'sign in', 'authenticate']):
            return "Authentication"
        elif any(word in task_lower for word in ['search', 'find', 'look for']):
            return "Search"
        elif any(word in task_lower for word in ['save', 'add', 'create', 'book']):
            return "Creation/Booking"
        elif any(word in task_lower for word in ['remove', 'delete', 'cancel']):
            return "Deletion/Cancellation"
        elif any(word in task_lower for word in ['navigate', 'go to', 'visit']):
            return "Navigation"
        else:
            return "General"
    
    async def _generate_guide_with_llm(
        self,
        task: str,
        rag_plans_context: str,
        navigation_graph_context: str,
        previous_guide_context: str,
        website_url: str,
        task_type: str,
        attempt_count: int
    ) -> str:
        """Génère le guide avec le LLM"""
        
        # Construire le prompt utilisateur
        user_prompt = GUIDE_GENERATION_USER_PROMPT_TEMPLATE.format(
            task=task,
            rag_plans_context=rag_plans_context,
            navigation_graph_context=navigation_graph_context,
            previous_guide_context=previous_guide_context,
            website_url=website_url,
            task_type=task_type,
            attempt_count=attempt_count
        )
        
        # Créer les messages
        system_message = SystemMessage(content=GUIDE_GENERATION_SYSTEM_PROMPT)
        user_message = UserMessage(content=user_prompt)
        
        # Appeler le LLM
        logger.info("🤖 Génération du guide avec le LLM...")
        response = await self.guide_llm.ainvoke([system_message, user_message])
        
        return response.completion
    
    def _generate_fallback_guide(self, task: str, previous_guide: Optional[str]) -> str:
        """Génère un guide de fallback en cas d'erreur"""
        fallback_parts = [
            "## Fallback Guide (Generated due to system error)",
            "",
            f"**Task:** {task}",
            "",
            "### Basic Approach:",
            "1. Navigate to the website",
            "2. Identify the main elements needed for the task",
            "3. Follow a logical sequence of actions",
            "4. Verify each step before proceeding",
            "5. Check for success indicators",
            ""
        ]
        
        if previous_guide:
            fallback_parts.extend([
                "### Previous Attempt Insights:",
                previous_guide,
                ""
            ])
        
        fallback_parts.append(
            "**Note:** This is a fallback guide. Consider reviewing the task "
            "and previous attempts for better guidance."
        )
        
        return "\n".join(fallback_parts)
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques du système"""
        try:
            rag_stats = self.rag_manager.get_plans_statistics()
            nav_stats = self.nav_manager.get_navigation_statistics()
            
            return {
                "rag": rag_stats,
                "navigation": nav_stats,
                "total_knowledge_items": rag_stats["total_plans"] + nav_stats["total_graphs"]
            }
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des statistiques: {e}")
            return {"rag": {}, "navigation": {}, "total_knowledge_items": 0} 