import textwrap

from browser_use.llm import ChatOpenAI
from browser_use import Agent, BrowserSession
from dotenv import load_dotenv
load_dotenv()

import asyncio

llm = ChatOpenAI(model="gpt-4.1")

async def main():
    # cdp_host = 'localhost'
    # cdp_host = 'vnc-desktop'
    cdp_host = '172.19.0.2'
    cdp_url = f'http://{cdp_host}:9222'
    browser_session = BrowserSession(cdp_url=cdp_url)

    task = textwrap.dedent("""
        How do you set up MLflow with a remote tracking server on AWS S3 for
        experiment tracking, then configure automated model deployment to Amazon
        SageMaker endpoints with A/B testing capabilities and model performance
        monitoring?
    """)

    agent = Agent(task=task, llm=llm, browser_session=browser_session)
    result = await agent.run()
    print(result)

asyncio.run(main())
