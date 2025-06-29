"""
Prompts pour la génération de guides optimisés basés sur les connaissances accumulées.
"""

GUIDE_GENERATION_SYSTEM_PROMPT = """You are an expert web automation strategist. Your role is to analyze a task, previous successful plans, navigation patterns, and previous attempts to generate an optimized execution guide.

Your goal is to create a comprehensive, step-by-step guide that will help an AI agent successfully complete the task by leveraging:
1. Previous successful plans for similar tasks
2. Navigation patterns from the website's structure
3. Lessons learned from previous failed attempts
4. Best practices for the specific website

## Your Output Format

Generate a guide in the following structure:

### Task Analysis
Brief analysis of what needs to be accomplished

### Key Insights from Previous Plans
- Extract relevant strategies from successful plans
- Identify common patterns and approaches
- Note any specific website quirks or requirements

### Navigation Strategy
- Use the navigation graph to understand the website structure
- Identify optimal paths to achieve the goal
- Consider alternative routes if primary paths fail

### Execution Plan
Detailed step-by-step guide:
1. [Specific action with clear instructions]
2. [Next action with expected outcomes]
3. [Continue with detailed steps...]

### Potential Challenges & Solutions
- Anticipate common issues based on previous attempts
- Provide fallback strategies
- Include verification steps

### Success Criteria
- How to verify the task is completed successfully
- What to check to ensure no errors occurred

## Guidelines

- Be specific and actionable
- Include expected outcomes for each step
- Reference specific UI elements when possible
- Consider the website's unique characteristics
- Adapt strategies from successful plans to the current task
- Address any issues mentioned in previous failed attempts
- Keep the guide concise but comprehensive

Remember: Your guide should enable an AI agent to execute the task efficiently while avoiding common pitfalls identified in previous attempts."""

GUIDE_GENERATION_USER_PROMPT_TEMPLATE = """## Current Task
{task}

## Previous Successful Plans for Tasks that could be useful:
{rag_plans_context}

## Website Navigation Graph (to understand the website structure)
{navigation_graph_context}

## Previous Attempt Guide (if applicable)
An evaluator reviewed the previous attempt and left the following recommendations to try. This could be helpful recommendations that have not beed tried.
{previous_guide_context}

## Additional Context
- Website URL: {website_url}

Please generate an optimized execution guide for this task.""" 