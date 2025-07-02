"""
Optimized guide generator based on accumulated knowledge.

This module generates optimized guides by combining:
1. RAG plans for similar tasks
2. Navigation graphs to understand website structure
3. Previous attempt guides
4. LLM-based guide generation
"""

import logging
import os
from typing import List, Dict, Any, Optional, Literal

from browser_use.llm import ChatAnthropic, ChatOpenAI
from browser_use.llm.messages import SystemMessage, UserMessage

from ..prompts.guide_generation_prompts import GUIDE_GENERATION_SYSTEM_PROMPT, GUIDE_GENERATION_USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class GuideGenerator:
    """Optimized guide generator service"""
    
    def __init__(self, llm_provider: Literal["anthropic", "openai"] = "anthropic"):
        """
        Initialize the guide generator
        
        Args:
            llm_provider: LLM provider ("anthropic" or "openai")
        """
        self.llm_provider = llm_provider
        
        # Initialize LLM for guide generation
        self.guide_llm = None
        
        if llm_provider == "anthropic":
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                self.guide_llm = ChatAnthropic(
                    model="claude-sonnet-4-20250514",
                    api_key=api_key,
                    max_tokens=4000,
                    temperature=0.2
                )
            else:
                logger.warning("⚠️ ANTHROPIC_API_KEY non défini, la génération de guides sera désactivée")
        elif llm_provider == "openai":
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.guide_llm = ChatOpenAI(
                    model="gpt-4o",
                    api_key=api_key,
                    max_tokens=4000,
                    temperature=0.2
                )
            else:
                logger.warning("⚠️ OPENAI_API_KEY non défini, la génération de guides sera désactivée")
        else:
            logger.warning(f"⚠️ Fournisseur LLM non reconnu: {llm_provider}, la génération de guides sera désactivée")
        
        logger.info(f"🎯 Guide Generator initialisé avec {llm_provider}")
    
    async def generate_optimized_guide(
        self,
        task: str,
        website_url: str,
        rag_plans_context: str = "",
        navigation_graph_context: str = "",
        previous_guide_context: str = "",
        attempt_count: int = 0
    ) -> str:
        """
        Generate an optimized guide for a given task
        
        Args:
            task: The task to execute
            website_url: Website URL
            rag_plans_context: Context from RAG plans (provided by caller)
            navigation_graph_context: Context from navigation graphs (provided by caller)
            previous_guide_context: Context from previous attempt (provided by caller)
            attempt_count: Number of previous attempts
            
        Returns:
            Generated optimized guide
        """
        try:
            logger.info("🔍 Generating optimized guide...")
            
            # Determine task type
            task_type = self._determine_task_type(task)

            # If no context at all, don't generate a guide
            if not rag_plans_context and not navigation_graph_context and not previous_guide_context:
                logger.info("🔍 No context provided, skipping guide generation")
                return ""
            
            # Generate optimized guide
            optimized_guide = await self._generate_guide_with_llm(
                task=task,
                rag_plans_context=rag_plans_context,
                navigation_graph_context=navigation_graph_context,
                previous_guide_context=previous_guide_context,
                website_url=website_url,
                task_type=task_type,
                attempt_count=attempt_count
            )
            
            logger.info("✅ Optimized guide generated successfully")
            return optimized_guide
            
        except Exception as e:
            logger.error(f"❌ Error generating guide: {e}")
            # Return fallback guide
            return self._generate_fallback_guide(task, previous_guide_context)
    
    def _determine_task_type(self, task: str) -> str:
        """Determine task type based on content"""
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
        """Generate guide with LLM"""
        
        # Vérifier si le LLM est disponible
        if not self.guide_llm:
            logger.warning("⚠️ LLM non disponible, utilisation du guide de fallback")
            return self._generate_fallback_guide(task, previous_guide_context)
        
        # Build user prompt
        user_prompt = GUIDE_GENERATION_USER_PROMPT_TEMPLATE.format(
            task=task,
            rag_plans_context=rag_plans_context,
            navigation_graph_context=navigation_graph_context,
            previous_guide_context=previous_guide_context,
            website_url=website_url,
            task_type=task_type,
            attempt_count=attempt_count
        )
        
        # Create messages
        system_message = SystemMessage(content=GUIDE_GENERATION_SYSTEM_PROMPT)
        user_message = UserMessage(content=user_prompt)
        
        # Call LLM
        logger.info("🤖 Generating guide with LLM...")
        response = await self.guide_llm.ainvoke([system_message, user_message])
        
        return response.completion
    
    def _generate_fallback_guide(self, task: str, previous_guide_context: str) -> str:
        """Generate fallback guide in case of error"""
        fallback_parts = [
            "## Fallback Guide (Generated due to system error)",
            "",
            f"**Task:** {task}",
            "",
            "### Basic Approach:",
            "1. Identify the main elements needed for the task",
            "2. Follow a logical sequence of actions",
            "3. Verify each step before proceeding",
            "4. Check for success indicators",
            ""
        ]
        
        if previous_guide_context and previous_guide_context != "No previous attempt guide available.":
            fallback_parts.extend([
                "### Previous Attempt Insights:",
                previous_guide_context,
                "This guide was previously used to try to complete the task but did not work.",
                ""
            ])
        
        fallback_parts.append(
            "**Note:** This is a fallback guide. Consider reviewing the task requirements carefully."
        )
        
        return "\n".join(fallback_parts) 