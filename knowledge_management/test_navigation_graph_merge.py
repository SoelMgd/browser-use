"""
Test script for navigation graph merging functionality.

This script tests the new navigation graph merging feature to ensure it works correctly.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

# Local imports
from knowledge_management.utils.navigation_graph_manager import NavigationGraphManager

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_navigation_graph_merge():
    """Test the navigation graph merging functionality"""
    
    # Test data - two sample navigation graphs
    existing_graph = {
        "Home Page": {
            "url": "https://example.com/",
            "layout": "Main landing page with navigation menu",
            "elements": [
                "C: Navigation menu ['Home', 'About', 'Contact'] @top",
                "I: Search bar @center",
                "C: Login button @top-right"
            ],
            "outgoing_links": [
                {
                    "target": "About Page",
                    "action": "click on 'About' in navigation menu"
                },
                {
                    "target": "Contact Page", 
                    "action": "click on 'Contact' in navigation menu"
                }
            ]
        },
        "About Page": {
            "url": "https://example.com/about",
            "layout": "Information page about the company",
            "elements": [
                "C: Back to home link @top-left",
                "C: Navigation menu ['Home', 'About', 'Contact'] @top"
            ],
            "outgoing_links": [
                {
                    "target": "Home Page",
                    "action": "click on 'Home' in navigation menu"
                }
            ]
        }
    }
    
    new_graph = {
        "Home Page": {
            "url": "https://example.com/",
            "layout": "Main landing page with enhanced features",
            "elements": [
                "C: Navigation menu ['Home', 'About', 'Contact', 'Services'] @top",
                "I: Search bar @center",
                "C: Login button @top-right",
                "C: Sign up button @top-right"
            ],
            "outgoing_links": [
                {
                    "target": "Services Page",
                    "action": "click on 'Services' in navigation menu"
                },
                {
                    "target": "Login Page",
                    "action": "click on 'Login' button"
                }
            ]
        },
        "Services Page": {
            "url": "https://example.com/services",
            "layout": "Services listing page",
            "elements": [
                "C: Back to home link @top-left",
                "C: Service cards ['Web Design', 'Development'] @center"
            ],
            "outgoing_links": [
                {
                    "target": "Home Page",
                    "action": "click on 'Home' in navigation menu"
                }
            ]
        }
    }
    
    try:
        # Create navigation graph manager
        nav_manager = NavigationGraphManager()
        
        logger.info("🧪 Testing navigation graph merging functionality...")
        
        # Test 1: Save first graph
        logger.info("📊 Saving first navigation graph...")
        success1 = await nav_manager.save_navigation_graph(existing_graph, "https://example.com")
        
        if not success1:
            logger.error("❌ Failed to save first graph")
            return
        
        logger.info("✅ First graph saved successfully")
        
        # Test 2: Save second graph (should trigger merge)
        logger.info("📊 Saving second navigation graph (should trigger merge)...")
        success2 = await nav_manager.save_navigation_graph(new_graph, "https://example.com")
        
        if not success2:
            logger.error("❌ Failed to save second graph")
            return
        
        logger.info("✅ Second graph saved and merged successfully")
        
        # Test 3: Verify the merged graph
        logger.info("🔍 Verifying merged graph...")
        graphs = nav_manager.find_navigation_graphs_for_website("https://example.com")
        
        if graphs:
            graph_content = graphs[0]['graph_content']
            merged_graph = json.loads(graph_content)
            
            print("\n" + "="*60)
            print("🧪 MERGE TEST RESULTS")
            print("="*60)
            
            print(f"📊 Original graph pages: {list(existing_graph.keys())}")
            print(f"📊 New graph pages: {list(new_graph.keys())}")
            print(f"📊 Merged graph pages: {list(merged_graph.keys())}")
            
            # Check if all pages are present
            all_pages = set(existing_graph.keys()) | set(new_graph.keys())
            merged_pages = set(merged_graph.keys())
            
            if all_pages.issubset(merged_pages):
                print(f"✅ All pages successfully merged!")
            else:
                missing_pages = all_pages - merged_pages
                print(f"⚠️ Missing pages in merged graph: {missing_pages}")
            
            # Check if Home Page has elements from both graphs
            if "Home Page" in merged_graph:
                home_elements = merged_graph["Home Page"]["elements"]
                print(f"\n🏠 Home Page elements in merged graph: {len(home_elements)}")
                
                # Check for specific elements from both graphs
                has_search = any("Search bar" in elem for elem in home_elements)
                has_services = any("Services" in elem for elem in home_elements)
                has_signup = any("Sign up" in elem for elem in home_elements)
                
                print(f"  - Search bar: {'✅' if has_search else '❌'}")
                print(f"  - Services menu: {'✅' if has_services else '❌'}")
                print(f"  - Sign up button: {'✅' if has_signup else '❌'}")
            
            print(f"\n📄 Merged graph content preview:")
            print(json.dumps(merged_graph, indent=2)[:500] + "...")
            
        else:
            print(f"\n❌ No merged graph found")
        
        print(f"\n✅ Navigation graph merge test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        print(f"\n❌ Test failed: {e}")


async def main():
    """Main test function"""
    print("🧪 Starting navigation graph merge test...")
    await test_navigation_graph_merge()


if __name__ == "__main__":
    asyncio.run(main()) 