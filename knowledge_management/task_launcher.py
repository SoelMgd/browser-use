# Goal: A general-purpose web navigation agent for tasks like flight booking and course searching.

import asyncio
import os
import sys

# Adjust Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()


from browser_use.agent.service import Agent
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.llm import ChatAnthropic

# Set LLM based on defined environment variables
if os.getenv('ANTHROPIC_API_KEY'):
	llm = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    )
else:
	raise ValueError('Failed to load Anthropic credentials')


browser_session = BrowserSession(
	browser_profile=BrowserProfile(
		headless=False,  # This is True in production
		minimum_wait_page_load_time=3,  # 3 on prod
		maximum_wait_page_load_time=10,  # 20 on prod
		viewport={'width': 1280, 'height': 1100},
		user_data_dir='~/.config/browseruse/profiles/default',
		#trace_path='./tmp/web_voyager_agent',
	)
)

# TASK = """
# Find the lowest-priced one-way flight from Cairo to Montreal on February 21, 2025, including the total travel time and number of stops. on https://www.google.com/travel/flights/
# """
# TASK = """
# Browse Coursera, which universities offer Master of Advanced Study in Engineering degrees? Tell me what is the latest application deadline for this degree? on https://www.coursera.org/"""
TASK = """
Find and book a hotel in Paris with suitable accommodations for a family of four (two adults and two children) offering free cancellation for the dates of July 14-21, 2025. on https://www.booking.com/
"""


async def main():
	agent = Agent(
		task=TASK,
		llm=llm,
		browser_session=browser_session,
		validate_output=True,
		enable_memory=False,
	)
	history = await agent.run(max_steps=25)
	history.save_to_file('./tmp/history.json')


if __name__ == '__main__':
	asyncio.run(main())
