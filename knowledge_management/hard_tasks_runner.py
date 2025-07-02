# Goal: Execute hard tasks from the WebBench dataset using Browser Use with GPT-4o

import asyncio
import os
import sys
import json
import base64
import csv
from pathlib import Path
from typing import List, Dict, Any

# Adjust Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

from browser_use.agent.service import Agent
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.llm import ChatOpenAI

# Set LLM based on defined environment variables
if os.getenv('OPENAI_API_KEY'):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.0
    )
else:
    raise ValueError('Failed to load OpenAI credentials')

# Configuration
CSV_FILE = "browser-use/knowledge_management/datasets/webbench_hitl_final.csv"
OUTPUT_DIR = "browser-use/knowledge_management/hard_tasks_results"
MAX_STEPS = 30

# Create output directories
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
Path(f"{OUTPUT_DIR}/screenshots").mkdir(parents=True, exist_ok=True)
Path(f"{OUTPUT_DIR}/results").mkdir(parents=True, exist_ok=True)
Path(f"{OUTPUT_DIR}/histories").mkdir(parents=True, exist_ok=True)

browser_session = BrowserSession(
    browser_profile=BrowserProfile(
        headless=False,  # Set to True in production
        minimum_wait_page_load_time=3,
        maximum_wait_page_load_time=10,
        viewport={'width': 1280, 'height': 1100},
        user_data_dir='~/.config/browseruse/profiles/default',
    )
)

def load_hard_tasks() -> List[Dict[str, Any]]:
    """Load hard tasks from the CSV file"""
    try:
        tasks = []
        total_tasks = 0
        hard_tasks_count = 0
        
        with open(CSV_FILE, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                total_tasks += 1
                if row['Difficulty'] == 'hard':
                    hard_tasks_count += 1
                    task = {
                        'id': str(row['ID']),
                        'starting_url': row['Starting URL'],
                        'category': row['Category'],
                        'difficulty': row['Difficulty'],
                        'task_description': row['Task']
                    }
                    tasks.append(task)
        
        print(f"Found {hard_tasks_count} hard tasks out of {total_tasks} total tasks")
        return tasks
    
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return []

def save_screenshots(history, task_id: str) -> List[str]:
    """Save screenshots from history and return list of saved file paths"""
    saved_files = []
    
    for i, history_item in enumerate(history.history):
        if history_item.state and history_item.state.screenshot:
            # Create filename
            filename = f"step_{i}.png"
            filepath = Path(f"{OUTPUT_DIR}/screenshots/{task_id}_{filename}")
            
            try:
                # Decode base64 and save
                screenshot_data = base64.b64decode(history_item.state.screenshot)
                with open(filepath, 'wb') as f:
                    f.write(screenshot_data)
                saved_files.append(str(filepath))
                print(f"  📸 Saved screenshot: {filename}")
            except Exception as e:
                print(f"  ❌ Error saving screenshot {filename}: {e}")
    
    return saved_files

def save_final_results(history, task_id: str):
    """Save final result and completion status"""
    try:
        # Get final result
        final_result = history.final_result()
        is_done = history.is_done()
        
        # Save final result
        result_file = Path(f"{OUTPUT_DIR}/results/{task_id}_final_result.txt")
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(str(final_result) if final_result else "No final result")
        
        # Save completion status
        status_file = Path(f"{OUTPUT_DIR}/results/{task_id}_completion_status.json")
        status_data = {
            'task_id': task_id,
            'is_done': is_done,
            'is_successful': history.is_successful(),
            'total_steps': len(history.history),
            'has_errors': history.has_errors(),
            'errors': history.errors()
        }
        
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        
        print(f"  💾 Saved final result and completion status")
        
    except Exception as e:
        print(f"  ❌ Error saving final results: {e}")

async def execute_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single task with Browser Use"""
    task_id = task['id']
    task_description = task['task_description']
    starting_url = task['starting_url']
    
    print(f"\n🚀 Executing Task {task_id}")
    print(f"   URL: {starting_url}")
    print(f"   Category: {task['category']}")
    print(f"   Task: {task_description[:100]}...")
    
    try:
        # Create agent
        agent = Agent(
            task=task_description,
            llm=llm,
            browser_session=browser_session,
            validate_output=True,
            enable_memory=False,
        )
        
        # Execute task
        history = await agent.run(max_steps=MAX_STEPS)
        
        # Save history
        history_file = Path(f"{OUTPUT_DIR}/histories/{task_id}_history.json")
        history.save_to_file(str(history_file))
        print(f"  📄 Saved history to: {history_file}")
        
        # Save screenshots
        screenshots = save_screenshots(history, task_id)
        
        # Save final results
        save_final_results(history, task_id)
        
        # Return execution summary
        return {
            'task_id': task_id,
            'success': True,
            'total_steps': len(history.history),
            'is_done': history.is_done(),
            'is_successful': history.is_successful(),
            'has_errors': history.has_errors(),
            'screenshots_count': len(screenshots),
            'final_result': history.final_result(),
            'error': None
        }
        
    except Exception as e:
        print(f"  ❌ Error executing task {task_id}: {e}")
        return {
            'task_id': task_id,
            'success': False,
            'total_steps': 0,
            'is_done': False,
            'is_successful': False,
            'has_errors': True,
            'screenshots_count': 0,
            'final_result': None,
            'error': str(e)
        }

async def main():
    """Main function to execute all hard tasks"""
    print("🔍 Loading hard tasks from CSV...")
    tasks = load_hard_tasks()
    
    if not tasks:
        print("❌ No hard tasks found or error loading CSV")
        return
    
    print(f"📋 Found {len(tasks)} hard tasks to execute")
    
    # Execute tasks
    results = []
    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*80}")
        print(f"Task {i}/{len(tasks)}")
        print(f"{'='*80}")
        
        result = await execute_task(task)
        results.append(result)
        
        # Small delay between tasks
        await asyncio.sleep(2)
    
    # Save overall results summary
    summary_file = Path(f"{OUTPUT_DIR}/execution_summary.json")
    summary = {
        'total_tasks': len(tasks),
        'successful_tasks': len([r for r in results if r['success']]),
        'failed_tasks': len([r for r in results if not r['success']]),
        'completed_tasks': len([r for r in results if r['is_done']]),
        'successful_completions': len([r for r in results if r['is_successful']]),
        'tasks_with_errors': len([r for r in results if r['has_errors']]),
        'total_screenshots': sum([r['screenshots_count'] for r in results]),
        'task_results': results
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print("📊 EXECUTION SUMMARY")
    print(f"{'='*80}")
    print(f"Total tasks: {summary['total_tasks']}")
    print(f"Successful executions: {summary['successful_tasks']}")
    print(f"Failed executions: {summary['failed_tasks']}")
    print(f"Completed tasks: {summary['completed_tasks']}")
    print(f"Successful completions: {summary['successful_completions']}")
    print(f"Tasks with errors: {summary['tasks_with_errors']}")
    print(f"Total screenshots saved: {summary['total_screenshots']}")
    print(f"\n📁 Results saved in: {OUTPUT_DIR}")
    print(f"📄 Summary saved to: {summary_file}")

if __name__ == '__main__':
    asyncio.run(main()) 