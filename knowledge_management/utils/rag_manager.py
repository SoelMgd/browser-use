#!/usr/bin/env python3
"""
Script utilitaire pour gérer la base RAG des plans de succès.
"""

import sys
import logging
from pathlib import Path

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ajouter le chemin du projet
sys.path.append(str(Path(__file__).parent.parent))

from utils.plan_rag_manager import PlanRAGManager

def main():
    """Fonction principale du gestionnaire RAG"""
    
    if len(sys.argv) < 2:
        print("Usage: python rag_manager.py <command> [options]")
        print("\nCommandes disponibles:")
        print("  list                    - Lister tous les plans")
        print("  stats                   - Afficher les statistiques")
        print("  clear                   - Supprimer tous les plans")
        print("  delete-website <url>    - Supprimer les plans d'un site")
        print("  delete-task <title>     - Supprimer les plans d'une tâche")
        print("  test-domain <url>       - Tester l'extraction de domaine")
        return
    
    command = sys.argv[1]
    rag_manager = PlanRAGManager()
    
    if command == "list":
        print("📋 Liste de tous les plans RAG:")
        print("=" * 50)
        plans = rag_manager.list_all_plans()
        
        if not plans:
            print("Aucun plan trouvé.")
        else:
            for i, plan in enumerate(plans, 1):
                print(f"\n{i}. {plan['task_title']}")
                print(f"   Site: {plan['website_url']}")
                print(f"   ID: {plan['task_id']}")
                print(f"   Date: {plan['execution_date']}")
                print(f"   Plan: {plan['plan_preview']}")
    
    elif command == "stats":
        print("📊 Statistiques de la base RAG:")
        print("=" * 50)
        stats = rag_manager.get_plans_statistics()
        print(f"Total plans: {stats['total_plans']}")
        print(f"Sites web uniques: {stats['unique_websites']}")
        if stats['websites']:
            print("Sites:")
            for site in stats['websites']:
                print(f"  - {site}")
    
    elif command == "clear":
        print("🗑️ Suppression de tous les plans...")
        success = rag_manager.clear_all_plans()
        if success:
            print("✅ Tous les plans ont été supprimés.")
        else:
            print("❌ Erreur lors de la suppression.")
    
    elif command == "delete-website":
        if len(sys.argv) < 3:
            print("❌ URL du site requise.")
            return
        website_url = sys.argv[2]
        print(f"🗑️ Suppression des plans pour {website_url}...")
        success = rag_manager.delete_plans_by_website(website_url)
        if success:
            print("✅ Plans supprimés.")
        else:
            print("❌ Erreur lors de la suppression.")
    
    elif command == "delete-task":
        if len(sys.argv) < 3:
            print("❌ Titre de la tâche requis.")
            return
        task_title = sys.argv[2]
        print(f"🗑️ Suppression des plans pour la tâche: {task_title}...")
        success = rag_manager.delete_plans_by_task_title(task_title)
        if success:
            print("✅ Plans supprimés.")
        else:
            print("❌ Erreur lors de la suppression.")
    
    elif command == "test-domain":
        if len(sys.argv) < 3:
            print("❌ URL requise pour le test.")
            return
        url = sys.argv[2]
        
        # Importer le NavigationGraphManager pour tester
        from navigation_graph_manager import NavigationGraphManager
        nav_manager = NavigationGraphManager()
        
        domain = nav_manager._extract_domain(url)
        print(f"🌐 Test d'extraction de domaine:")
        print(f"URL: {url}")
        print(f"Domaine extrait: {domain}")
        print(f"Nom de fichier généré: {domain}_graph.json")
    
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Utilisez 'python rag_manager.py' pour voir les commandes disponibles.")

if __name__ == "__main__":
    main() 