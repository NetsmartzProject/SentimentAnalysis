# import uvicorn
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from src.routes import agent

# app = FastAPI(
#     title="SQL Assistant API",
#     description="An API for interacting with a SQL database through natural language",
#     version="1.0.0",
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )



from agno.agent import Agent
from agno.models.groq import Groq
from agno.tools.duckduckgo import DuckDuckGoTools
from dotenv import load_dotenv
 
load_dotenv()
 
agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    description="You are AI assistant, give me the news api for free and give me the api where i can test it on the postman",
    tools=[DuckDuckGoTools()],
    markdown=True
)
 
try:
    agent.print_response("TESLA.")
except Exception as e:
    print("Sorry, I am unable to process your input at the moment.")
 