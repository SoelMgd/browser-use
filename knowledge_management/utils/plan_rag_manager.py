"""
RAG Manager for successful task plans.

This module allows to:
1. Store successful plans with their metadata in a vector database
2. Search for similar plans based on task_title
3. Retrieve the most relevant plans for a new task
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)


class PlanRAGManager:
    """RAG Manager for successful plans"""
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize the RAG manager
        
        Args:
            storage_dir: Storage directory for the vector database
        """
        if storage_dir is None:
            storage_dir = Path(__file__).parent.parent / "rag_storage"
        
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.storage_dir / "chroma_db"),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collection for plans
        self.plans_collection = self.chroma_client.get_or_create_collection(
            name="successful_plans",
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"📚 RAG Manager initialized with storage: {self.storage_dir}")
    
    def _create_plan_document(self, task_title: str, plan: str, 
                             task_id: str, execution_date: str) -> Dict[str, Any]:
        """
        Create a plan document for storage
        
        Args:
            task_title: Generalized task title (will be embedded as-is)
            plan: The successful plan
            task_id: Unique task ID
            execution_date: Execution date
            
        Returns:
            Structured document for storage
        """
        return {
            "task_title": task_title,
            "plan": plan,
            "task_id": task_id,
            "execution_date": execution_date,
            "text_for_embedding": task_title  # Use task_title directly for embedding
        }
    
    def store_successful_plan(self, plans_dict: Dict[str, str], task_id: str) -> bool:
        """
        Store successful plans in the vector database
        
        Args:
            plans_dict: Dictionary of plans with titles as keys and plan content as values
            task_id: Unique task ID
            
        Returns:
            True if storage was successful for all plans
        """
        if not plans_dict:
            logger.warning("⚠️ No plans to store")
            return True
        
        success_count = 0
        total_count = len(plans_dict)
        
        try:
            execution_date = datetime.now().isoformat()
            
            for task_title, plan_content in plans_dict.items():
                try:
                    # Create document for this plan
                    document = self._create_plan_document(
                        task_title, plan_content, task_id, execution_date
                    )
                    
                    # Generate embedding from task_title
                    embedding = self.embedding_model.encode(document["text_for_embedding"])
                    
                    # Store in ChromaDB
                    self.plans_collection.add(
                        embeddings=[embedding.tolist()],
                        documents=[document["text_for_embedding"]],
                        metadatas=[{
                            "task_title": task_title,
                            "plan": plan_content,
                            "task_id": task_id,
                            "execution_date": execution_date
                        }],
                        ids=[f"plan_{task_id}_{task_title}_{datetime.now().timestamp()}"]
                    )
                    
                    success_count += 1
                    logger.info(f"💾 Plan stored in RAG: {task_title}")
                    
                except Exception as e:
                    logger.error(f"❌ Error storing plan '{task_title}': {e}")
                    continue
            
            if success_count == total_count:
                logger.info(f"✅ All {total_count} plans stored successfully")
                return True
            elif success_count > 0:
                logger.warning(f"⚠️ {success_count}/{total_count} plans stored successfully")
                return True
            else:
                logger.error(f"❌ Failed to store any of the {total_count} plans")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in store_successful_plan: {e}")
            return False
    
    def find_similar_plans(self, task_title: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar plans for a given task
        
        Args:
            task_title: Title of the new task (will be embedded as-is)
            top_k: Number of plans to return
            
        Returns:
            List of similar plans with their metadata
        """
        try:
            logger.info(f"🔍 Searching similar plans for: {task_title}")
            # Generate embedding from task_title directly
            query_embedding = self.embedding_model.encode(task_title)
            
            # Search in ChromaDB
            results = self.plans_collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=top_k
            )
            
            # Format results
            similar_plans = []
            if results['metadatas'] and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    similar_plans.append({
                        "task_title": metadata["task_title"],
                        "plan": metadata["plan"],
                        "task_id": metadata["task_id"],
                        "execution_date": metadata["execution_date"],
                        "similarity_score": results['distances'][0][i] if results['distances'] else None
                    })
            
            logger.info(f"🔍 Found {len(similar_plans)} similar plans for {task_title}")
            return similar_plans
            
        except Exception as e:
            logger.error(f"❌ Error searching for similar plans: {e}")
            return []
    
    def build_context_from_similar_plans(self, similar_plans: List[Dict[str, Any]]) -> str:
        """
        Build context from similar plans
        
        Args:
            similar_plans: List of similar plans
            
        Returns:
            Formatted context for prompt injection
        """
        if not similar_plans:
            return ""
        
        context_parts = [
            "## The user found potential helpful guides for this task:",
            ""
        ]
        
        for i, plan_data in enumerate(similar_plans, 1):
            context_parts.extend([
                f"### Guide {i}: {plan_data['task_title']}",
                "",
                plan_data['plan'],
                ""
            ])
        
        context_parts.append(
            "If useful, use these previous successful plans as reference to improve your approach "
        )
        
        return "\n".join(context_parts)
    
    def get_plans_statistics(self) -> Dict[str, Any]:
        """
        Return statistics on stored plans
        
        Returns:
            Plan statistics
        """
        try:
            count = self.plans_collection.count()
            
            # Get all plans for statistics
            all_plans = self.plans_collection.get()
            
            task_titles = set()
            if all_plans['metadatas']:
                for metadata in all_plans['metadatas']:
                    task_titles.add(metadata['task_title'])
            
            return {
                "total_plans": count,
                "unique_task_titles": len(task_titles),
                "task_titles": list(task_titles)
            }
            
        except Exception as e:
            logger.error(f"❌ Error retrieving statistics: {e}")
            return {"total_plans": 0, "unique_task_titles": 0, "task_titles": []}
    
    def clear_all_plans(self) -> bool:
        """
        Remove all plans from the RAG database
        
        Returns:
            True if cleanup was successful
        """
        try:
            # Get all IDs to delete them
            results = self.plans_collection.get()
            if results['ids']:
                # Delete all elements by their IDs
                self.plans_collection.delete(ids=results['ids'])
                logger.info(f"🗑️ {len(results['ids'])} RAG plans have been deleted")
            else:
                logger.info("🗑️ No plans to delete")
            return True
        except Exception as e:
            logger.error(f"❌ Error cleaning RAG database: {e}")
            return False
    
    def delete_plans_by_task_title(self, task_title: str) -> bool:
        """
        Delete all plans with a given task title
        
        Args:
            task_title: Task title
            
        Returns:
            True if deletion was successful
        """
        try:
            # Delete plans with this title
            self.plans_collection.delete(where={"task_title": task_title})
            logger.info(f"🗑️ Plans deleted for task: {task_title}")
            return True
        except Exception as e:
            logger.error(f"❌ Error deleting plans for {task_title}: {e}")
            return False
    
    def list_all_plans(self) -> List[Dict[str, Any]]:
        """
        List all plans stored in the RAG database
        
        Returns:
            List of all plans with their metadata
        """
        try:
            # Get all plans
            results = self.plans_collection.get()
            
            plans = []
            if results['metadatas']:
                for i, metadata in enumerate(results['metadatas']):
                    plans.append({
                        'task_title': metadata.get('task_title', 'Unknown'),
                        'task_id': metadata.get('task_id', 'Unknown'),
                        'execution_date': metadata.get('execution_date', 'Unknown'),
                        'plan_preview': metadata.get('plan', '')[:100] + '...' if metadata.get('plan') else 'No plan'
                    })
            
            return plans
        except Exception as e:
            logger.error(f"❌ Error retrieving plans: {e}")
            return [] 