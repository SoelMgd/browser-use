"""
Utilitaires pour tester et gérer le système RAG des plans de succès.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

from knowledge_management.utils.plan_rag_manager import PlanRAGManager

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_rag_system():
    """Teste le système RAG avec des données d'exemple"""
    
    # Initialiser le gestionnaire RAG
    rag_manager = PlanRAGManager()
    
    # Données de test
    test_plans = [
        {
            "task_title": "Login and save property to wishlist",
            "website_url": "http://airbnb.com",
            "plan": """1. Navigate to airbnb.com
2. Click on 'Log in' button
3. Enter credentials: username 'soel@twin.so', password 'Agent123456!'
4. Search for a property with 'Guest Favorite' badge
5. Click on the property to view details
6. Click 'Save' button to add to wishlist
7. Verify the property appears in wishlist""",
            "task_id": "test_001"
        },
        {
            "task_title": "Remove property from wishlist",
            "website_url": "http://airbnb.com", 
            "plan": """1. Log in to airbnb.com
2. Navigate to 'Wishlist' section
3. Find the previously saved property
4. Click on the property to open details
5. Click 'Remove from wishlist' button
6. Confirm removal
7. Verify property is no longer in wishlist""",
            "task_id": "test_002"
        },
        {
            "task_title": "Search and filter properties",
            "website_url": "http://airbnb.com",
            "plan": """1. Go to airbnb.com homepage
2. Enter destination in search bar
3. Set check-in and check-out dates
4. Add number of guests
5. Click 'Search' button
6. Use filters to narrow results (price, amenities, etc.)
7. Sort by rating or price
8. Browse through filtered results""",
            "task_id": "test_003"
        }
    ]
    
    print("🧪 Test du système RAG")
    print("=" * 50)
    
    # Stocker les plans de test
    print("\n📥 Stockage des plans de test...")
    for plan_data in test_plans:
        success = rag_manager.store_successful_plan(
            plan_data["task_title"],
            plan_data["website_url"], 
            plan_data["plan"],
            plan_data["task_id"]
        )
        print(f"  Plan '{plan_data['task_title']}': {'✅' if success else '❌'}")
    
    # Afficher les statistiques
    print("\n📊 Statistiques:")
    stats = rag_manager.get_plans_statistics()
    print(f"  Plans stockés: {stats['total_plans']}")
    print(f"  Sites web: {stats['unique_websites']}")
    
    # Tester la recherche
    print("\n🔍 Test de recherche de plans similaires...")
    
    test_queries = [
        ("Login and manage wishlist", "http://airbnb.com"),
        ("Search for properties", "http://airbnb.com"),
        ("Book a property", "http://airbnb.com")
    ]
    
    for query_title, query_url in test_queries:
        print(f"\n  Recherche: '{query_title}' sur {query_url}")
        similar_plans = rag_manager.find_similar_plans(query_title, query_url, top_k=2)
        
        if similar_plans:
            for i, plan in enumerate(similar_plans, 1):
                print(f"    {i}. {plan['task_title']} (score: {plan['similarity_score']:.3f})")
        else:
            print("    Aucun plan similaire trouvé")
    
    # Tester la génération de contexte
    print("\n📝 Test de génération de contexte...")
    similar_plans = rag_manager.find_similar_plans("Login and save property", "http://airbnb.com")
    if similar_plans:
        context = rag_manager.build_context_from_similar_plans(similar_plans)
        print("  Contexte généré:")
        print("  " + "\n  ".join(context.split('\n')[:10]) + "...")
    
    print("\n✅ Test terminé!")


def list_stored_plans():
    """Liste tous les plans stockés dans le système RAG"""
    
    rag_manager = PlanRAGManager()
    stats = rag_manager.get_plans_statistics()
    
    print("📚 Plans stockés dans le système RAG")
    print("=" * 50)
    print(f"Total: {stats['total_plans']} plans")
    print(f"Sites web: {stats['unique_websites']}")
    
    if stats['websites']:
        print(f"Sites: {', '.join(stats['websites'])}")
    
    # Récupérer tous les plans
    try:
        all_plans = rag_manager.plans_collection.get()
        if all_plans['metadatas']:
            print(f"\n📋 Détail des plans:")
            for i, metadata in enumerate(all_plans['metadatas'], 1):
                print(f"  {i}. {metadata['task_title']}")
                print(f"     Site: {metadata['website_url']}")
                print(f"     ID: {metadata['task_id']}")
                print(f"     Date: {metadata['execution_date']}")
                print(f"     Plan: {metadata['plan'][:100]}...")
                print()
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des plans: {e}")


def search_plans(query_title: str, website_url: str, top_k: int = 3):
    """Recherche des plans similaires"""
    
    rag_manager = PlanRAGManager()
    
    print(f"🔍 Recherche de plans similaires")
    print("=" * 50)
    print(f"Requête: '{query_title}' sur {website_url}")
    print(f"Nombre de résultats: {top_k}")
    print()
    
    similar_plans = rag_manager.find_similar_plans(query_title, website_url, top_k)
    
    if similar_plans:
        for i, plan in enumerate(similar_plans, 1):
            print(f"📋 Plan {i}:")
            print(f"  Titre: {plan['task_title']}")
            print(f"  Site: {plan['website_url']}")
            print(f"  ID: {plan['task_id']}")
            print(f"  Score de similarité: {plan['similarity_score']:.3f}")
            print(f"  Date: {plan['execution_date']}")
            print(f"  Plan: {plan['plan']}")
            print()
    else:
        print("❌ Aucun plan similaire trouvé")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_rag_system()
        elif command == "list":
            list_stored_plans()
        elif command == "search" and len(sys.argv) >= 4:
            query_title = sys.argv[2]
            website_url = sys.argv[3]
            top_k = int(sys.argv[4]) if len(sys.argv) > 4 else 3
            search_plans(query_title, website_url, top_k)
        else:
            print("Usage:")
            print("  python rag_utils.py test          # Test du système")
            print("  python rag_utils.py list          # Lister les plans")
            print("  python rag_utils.py search <title> <url> [top_k]  # Rechercher")
    else:
        test_rag_system() 