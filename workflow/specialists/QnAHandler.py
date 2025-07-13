from data.milvus.indexing import MilvusIndexer
import os

from llm.base import AgentClient
from pydantic_ai.models.gemini import GeminiModel
from pydantic_ai.providers.google_gla import GoogleGLAProvider

from data.cache.memory_handler import MessageMemoryHandler

import chainlit as cl

from utils.basetools import *

class QnAHandlerAgent(AgentClient):
    def __init__(self, collection_name: str):
        # Initialize Milvus indexer (run only once to create collection and index data)
        # Comment this out after first run
        indexer = MilvusIndexer(collection_name=collection_name, faq_file="src/data/mock_data/VNU_HCMUT_FAQ.xlsx")
        indexer.run()

        provider = GoogleGLAProvider(api_key=os.getenv("GEMINI_API_KEY"))
        model = GeminiModel('gemini-2.0-flash', provider=provider)

        # Initialize your tool 
        #---------------------------------------------
        faq_tool = create_faq_tool(collection_name=collection_name)
        #---------------------------------------------

        self.agent = AgentClient(
            model=model,
            system_prompt="Bạn là trợ lý ảo thông minh của VNU-HCMUT, có nhiệm vụ trả lời câu hỏi của sinh viên dựa trên cơ sở dữ liệu FAQ về quy định và chính sách của trường.",
            tools=[faq_tool]
        ).create_agent()

    def run(self, query: str):
        """Run the QnA handler agent with the provided query."""
        response = self.agent.run(query)
        return response