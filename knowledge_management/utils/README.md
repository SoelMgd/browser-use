# Knowledge Management Utils

This directory contains utility modules for the knowledge management system in Browser-Use.

## File Structure

### Core Parsers

#### `llm_response_parser.py`
**Purpose**: Parses LLM evaluator responses to extract structured data.

**Key Components**:
- `ParsedLLMResponse`: Dataclass containing parsed evaluation results
class ParsedLLMResponse:
    navigation_graph: Dict[str, Any]
    verdict: str
    guide: Dict[str, Any]
    failure_guide: str
    raw_response: str
    task_label: str  # First element of the tuple (SUCCESS, FAILURE, IMPOSSIBLE)
    website_url: str  # Second element of the tuple (main URL)
    task_title: str  # Third element of the tuple (generalized title)

- `LLMResponseParser`: Main parser class with methods to extract:
  - Navigation graph (JSON)
  - Verdict and task status
  - Failure guide (optional)
  - Guides learnt
  - Task metadata (label, URL, title)

**Usage**:
```python
from llm_response_parser import parse_llm_evaluation_response

parsed = parse_llm_evaluation_response(llm_response)
print(f"Status: {parsed.task_label}")
print(f"Navigation pages: {len(parsed.navigation_graph)}")
```

#### `history_parser.py`
**Purpose**: Converts Browser-Use history data to LLM-compatible messages.

**Key Functions**:
- `load_history_from_file()`: Loads history from JSON file
- `history_to_llm_messages()`: Converts history to LLM message format
- `save_all_screenshots()`: Extracts and saves screenshots from history

### Knowledge Storage

#### `plan_rag_manager.py`
**Purpose**: Manages successful task plans in a vector database using RAG (Retrieval-Augmented Generation).

**Key Features**:
- Stores task plans with semantic embeddings
- Searches for similar plans based on task titles
- Uses ChromaDB for vector storage
- Provides context building for LLM prompts

**Main Methods**:
- `store_successful_plan(plans_dict, task_id)`: Store multiple plans from a dictionary
- `find_similar_plans(task_title, top_k=10)`: Find similar plans
- `build_context_from_similar_plans()`: Build LLM context from plans
- `get_plans_statistics()`: Get database statistics

#### `navigation_graph_manager.py`
**Purpose**: Manages navigation graphs extracted from user interactions.

**Key Features**:
- Saves navigation graphs as JSON files
- Finds graphs for specific websites
- Builds context from multiple graphs
- Handles URL normalization and matching

**Main Methods**:
- `save_navigation_graph(graph, website_url)`: Save a navigation graph
- `find_navigation_graphs_for_website(url)`: Find graphs for a website
- `build_navigation_context(graphs)`: Build context from graphs

### Context Builders

#### `guide_generator.py`
**Purpose**: Generates optimized guides for task execution using LLM.

**Key Features**:
- Pure service that receives contexts as parameters
- Generates context-aware guides for task execution
- No direct data management dependencies

**Main Methods**:
- `generate_optimized_guide(task, website_url, rag_plans_context, navigation_graph_context, previous_guide_context, attempt_count)`: Generate guide with provided contexts

## Data Flow

1. **Task Execution**: Browser-Use executes a task and generates history
2. **History Parsing**: `history_parser.py` converts history to LLM messages
3. **Evaluation**: LLM evaluator analyzes the execution and generates response
4. **Response Parsing**: `llm_response_parser.py` extracts structured data
5. **Knowledge Storage**: 
   - Navigation graphs saved via `navigation_graph_manager.py`
   - Successful plans stored via `plan_rag_manager.py`
6. **Context Building** (for subsequent attempts): `TaskEvaluator` builds contexts from:
   - Previous navigation graphs via `navigation_graph_manager.py`
   - Similar plans from RAG via `plan_rag_manager.py`
   - Failure recommendations from evaluator
7. **Guide Generation**: `guide_generator.py` receives contexts and creates optimized guides

## File Formats

### Navigation Graph JSON
```json
{
  "Page Name": {
    "url": "https://example.com/page",
    "layout": "Page description",
    "elements": [
      "C: Clickable elements @location",
      "I: Input fields @location"
    ],
    "outgoing_links": [
      {
        "target": "Next Page",
        "action": "Action description"
      }
    ]
  }
}
```

### Plan RAG Storage
- **Embedding**: Task title is embedded directly
- **Metadata**: Includes task_title, plan content, task_id, execution_date
- **Search**: Semantic similarity based on task titles

### LLM Response Format
- **Navigation Graph**: JSON block before `<verdict>`
- **Verdict**: `<verdict>...</verdict>` with task status and tuple
- **Failure Guide**: `<failure_guide>...</failure_guide>` (optional)
- **Guides**: JSON block after verdict with reusable lessons

## Dependencies

- `sentence_transformers`: For semantic embeddings
- `chromadb`: For vector database storage
- `numpy`: For numerical operations
- `pathlib`: For file path handling
- `logging`: For system logging

## Usage Example

```python
from utils.plan_rag_manager import PlanRAGManager
from utils.navigation_graph_manager import NavigationGraphManager
from utils.llm_response_parser import parse_llm_evaluation_response

# Initialize managers
rag_manager = PlanRAGManager()
nav_manager = NavigationGraphManager()

# Store successful plan
plans_dict = {
    "Login to Airbnb and search properties": "1. Go to airbnb.com\n2. Click login\n3. Enter credentials",
    "Filter search results": "1. Use left sidebar filters\n2. Select amenities\n3. Apply filters"
}
rag_manager.store_successful_plan(plans_dict, "task_001")

# Find similar plans
similar_plans = rag_manager.find_similar_plans("Login and search")
context = rag_manager.build_context_from_similar_plans(similar_plans) 