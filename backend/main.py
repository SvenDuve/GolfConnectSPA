from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from langchain.chat_models import ChatOpenAI
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain,RouterOutputParser
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain



app = FastAPI()

origins = [
    "http://localhost:3000",  # React's default port
    "http://127.0.0.1:3000",
    # Add other origins/ports as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows access from specified origins
    allow_credentials=True,
    allow_methods=["*"],    # Allows all methods
    allow_headers=["*"],    # Allows all headers
)

import os
import openai
from dotenv import load_dotenv, find_dotenv

load_dotenv()
#_ = load_dotenv(find_dotenv()) # read local .env file
openai.api_key = os.environ['OPENAI_API_KEY']


MULTI_PROMPT_ROUTER_TEMPLATE = """Given a raw text input to a \
language model select the model prompt best suited for the input. \
You will be given the names of the available prompts and a \
description of what the prompt is best suited for. \
You may also revise the original input if you think that revising\
it will ultimately lead to a better response from the language model.

<< FORMATTING >>
Return a markdown code snippet with a JSON object formatted to look like:
```json
{{{{
    "destination": string \ name of the prompt to use or "DEFAULT"
    "next_inputs": string \ a potentially modified version of the original input
}}}}
```

REMEMBER: "destination" MUST be one of the candidate prompt \
names specified below OR it can be "DEFAULT" if the input is not\
well suited for any of the candidate prompts.
REMEMBER: "next_inputs" can just be the original input \
if you don't think any modifications are needed.

<< CANDIDATE PROMPTS >>
{destinations}

<< INPUT >>
{{input}}

<< OUTPUT (remember to include the ```json)>>"""


# account for deprecation of LLM model
import datetime
# Get the current date
current_date = datetime.datetime.now().date()

# Define the date after which the model should be set to "gpt-3.5-turbo"
target_date = datetime.date(2024, 6, 12)

# Set the model variable based on the current date
if current_date > target_date:
    llm_model = "gpt-3.5-turbo"
else:
    llm_model = "gpt-3.5-turbo-0301"


llm = ChatOpenAI(temperature=0.9, model=llm_model)


class TextRequest(BaseModel):
    text: str

@app.post("/process/")
async def process_text(request: TextRequest):
    try:
        user_text = request.text
        # Process the text with your LLM here
        print(user_text)
        llm_engine = set_llm_engine()
        # Placeholder response
        user_text = llm_engine.run(user_text)
        response = {"processed_text": user_text}
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

def set_llm_engine():
    # Call your LLM here
    putting_template = """You are a very smart golf putting instructor. \
    You are great at answering questions about putting and reading greens in a concise\
    and easy to understand manner. \
    When you don't know the answer to a question you admit\
    that you don't know.

    Here is a question:
    {input}"""


    short_game_template = """You are a very good golf short game instructor. \
    You are great at answering questions about chipping, pitching, shaping shots, different lies within 100 yards of the green, bunker play and other short game aspects. \
    You are so good because you are able to break down \
    hard problems into their component parts, 
    answer the component parts, and then put them together\
    to answer the broader question.

    Here is a question:
    {input}"""

    full_swing_template = """You are a very good golf instructor. \
    You have an excellent knowledge of and understanding shot making, iron play, wood play,\
    shaping shots and a vast library of drills to improve the golf swing. \
    You are good because you have the experience as a golf pro and have taught many students. \
    You are able to break down hard problems into their component parts, answer the component parts, and then put them together to answer the broader question.

    Here is a question:
    {input}"""


    strategic_template = """ You are a very good golf player and strategic instructor.\
    You are great at answering questions about course management, \
    strategy, and mental game. \
    You are so good because you have the experience as a golf pro and have played many tournaments. \
    You are able to break down hard problems into their component parts, answer the component parts, and then put them together to answer the broader question.

    Here is a question:
    {input}"""


    prompt_infos = [
        {
            "name": "putting", 
            "description": "Good for answering questions putting in golf", 
            "prompt_template": putting_template
        },
        {
            "name": "short_game", 
            "description": "Good for answering short game questions in golf", 
            "prompt_template": short_game_template
        },
        {
            "name": "full_swing", 
            "description": "Good for answering full swing questions in golf", 
            "prompt_template": full_swing_template
        },
        {
            "name": "strategic", 
            "description": "Good for answering strategic questions in golf", 
            "prompt_template": strategic_template
        }
    ]

    destination_chains = {}
    for p_info in prompt_infos:
        name = p_info["name"]
        prompt_template = p_info["prompt_template"]
        prompt = ChatPromptTemplate.from_template(template=prompt_template)
        chain = LLMChain(llm=llm, prompt=prompt)
        destination_chains[name] = chain  
    
    destinations = [f"{p['name']}: {p['description']}" for p in prompt_infos]
    destinations_str = "\n".join(destinations)

    default_prompt = ChatPromptTemplate.from_template("{input}")
    default_chain = LLMChain(llm=llm, prompt=default_prompt)


    router_template = MULTI_PROMPT_ROUTER_TEMPLATE.format(
        destinations=destinations_str
    )

    router_prompt = PromptTemplate(
        template=router_template,
        input_variables=["input"],
        output_parser=RouterOutputParser(),
    )

    router_chain = LLMRouterChain.from_llm(llm, router_prompt)


    return MultiPromptChain(router_chain=router_chain, destination_chains=destination_chains, default_chain=default_chain)#, verbose=True