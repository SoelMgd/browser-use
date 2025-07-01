#!/usr/bin/env python3
"""
Test script for the complete system with the new simplified implementation.
"""

import json
import logging
from pathlib import Path

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project path
import sys
sys.path.append(str(Path(__file__).parent))

from utils.navigation_graph_manager import NavigationGraphManager
from utils.plan_rag_manager import PlanRAGManager

def test_complete_system():
    """Test the complete system with the new implementation"""
    
    print("🧪 Testing the simplified complete system")
    print("=" * 50)
    
    # Create managers
    nav_manager = NavigationGraphManager()
    rag_manager = PlanRAGManager()
    
    # Test 0: Clear RAG database
    print("\n🗑️ Test 0: Clear RAG database")
    print("-" * 40)
    
    success = rag_manager.clear_all_plans()
    print(f"  RAG database cleared: {'✅' if success else '❌'}")
    
    # Verify database is empty
    rag_stats = rag_manager.get_plans_statistics()
    print(f"  Plans in database: {rag_stats['total_plans']}")
    
    # Test 1: Save navigation graph
    print("\n📊 Test 1: Save navigation graph")
    print("-" * 40)
    
    test_graph = {
        "Home Page": {
            "url": "https://www.airbnb.com/",
            "layout": "Main Airbnb homepage",
            "elements": [
                "C: Property cards with 'Guest favorite' badges @grid-layout",
                "C: 'Log in or sign up' button @bottom-center"
            ],
            "outgoing_links": [
                {
                    "target": "Login Modal",
                    "action": "click on 'Log in or sign up' button"
                }
            ]
        },
        "Login Modal": {
            "url": "https://www.airbnb.com/",
            "layout": "Modal overlay for user authentication",
            "elements": [
                "I: Email input field @center",
                "I: Password input field @center",
                "C: Continue/Login button @bottom-of-modal"
            ],
            "outgoing_links": [
                {
                    "target": "Home Page",
                    "action": "successful login returns to homepage"
                }
            ]
        }
    }
    
    # Save graph
    success = nav_manager.save_navigation_graph(test_graph, "http://airbnb.com")
    print(f"  Graph save: {'✅' if success else '❌'}")
    
    # Test 2: Search saved graph
    print("\n🔍 Test 2: Search saved graph")
    print("-" * 40)
    
    graphs = nav_manager.find_navigation_graphs_for_website("http://airbnb.com")
    print(f"  Graphs found: {len(graphs)}")
    
    if graphs:
        graph_info = graphs[0]
        print(f"    File: {graph_info['file_path']}")
        print(f"    Content length: {len(graph_info['graph_content'])} chars")
        print(f"    Graph content preview: {graph_info['graph_content']}...")

    
    # Test 3: Generate context
    print("\n📝 Test 3: Generate context")
    print("-" * 40)
    
    if graphs:
        context = nav_manager.build_navigation_context(graphs)
        print("  Generated context:")
        print("  " + "\n  ".join(context.split('\n')))
        print(f"  Total length: {len(context)} characters")
    else:
        print("  No graph available")
    
    # Test 4: Test with different URLs
    print("\n🌐 Test 4: Test with different URLs")
    print("-" * 40)
    
    test_urls = [
        "http://airbnb.com",
        "https://www.airbnb.com",
        "https://airbnb.subdomain.com",
        "https://subdomain.airbnb.com/search",
        "https://admin.airbnb.com",
        "http://booking.com"
    ]
    
    for url in test_urls:
        graphs = nav_manager.find_navigation_graphs_for_website(url)
        print(f"  {url}: {len(graphs)} graph(s)")
        if graphs:
            print(f"    → Found: {graphs[0]['file_path']}")
    
    # Test 5: Test RAG system
    print("\n📚 Test 5: Test RAG system")
    print("-" * 40)
    
    # Save test plan
    test_plans = {
        "Login and search properties on Airbnb": "1. Navigate to airbnb.com\n2. Click login button\n3. Enter credentials\n4. Search for properties",
        "Filter properties by amenities": "1. On search results page\n2. Scroll to filters section\n3. Select desired amenities\n4. Apply filters"
    }
    
    success = rag_manager.store_successful_plan(test_plans, "test_001")
    print(f"  RAG plan save: {'✅' if success else '❌'}")
    
    # Search similar plans
    similar_plans = rag_manager.find_similar_plans("Login and search properties")
    print(f"  Similar plans found: {len(similar_plans)}")
    
    if similar_plans:
        plan = similar_plans[0]
        print(f"    Title: {plan['task_title']}")
        print(f"    Score: {plan['similarity_score']}")
    
    # Test 6: Statistics
    print("\n📊 Test 6: Statistics")
    print("-" * 40)
    
    rag_stats = rag_manager.get_plans_statistics()
    print(f"  RAG plans: {rag_stats['total_plans']}")
    print(f"  Unique task titles (RAG): {rag_stats['unique_task_titles']}")
    
    # Count navigation graphs
    nav_graphs = list(nav_manager.graphs_dir.glob("*_graph.json"))
    print(f"  Navigation graphs: {len(nav_graphs)}")
    for graph_file in nav_graphs:
        print(f"    {graph_file.name}")
    
    print("\n✅ Test completed!")

if __name__ == "__main__":
    test_complete_system() 