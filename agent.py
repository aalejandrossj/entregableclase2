import os
import re
import math
import json
from dotenv import load_dotenv

from groq import Groq

from tool import tool
from utils.extraction import extract_tag_content


# cargamos las variables de entorno, ahi debera estar nuestra API de Groq
load_dotenv()

MODEL = "llama-3.3-70b-versatile"
GROQ_CLIENT = Groq()

BASE_SYSTEM_PROMPT = ""   

# Define the System Prompt as a constant
REACT_SYSTEM_PROMPT = """
You are a function calling AI model. You operate by running a loop with the following steps: Thought, Action, Observation.
You are provided with function signatures within <tools></tools> XML tags.
You may call one or more functions to assist with the user query. Don't make assumptions about what values to plug into functions. Pay special attention to the properties 'types'. You should use those types as in a Python dict.

For each function call return a JSON object with the function name and arguments within <tool_call></tool_call> XML tags as follows:

<tool_call> {"name": <function-name>, "arguments": <args-dict>, "id": <monotonically-increasing-id>} </tool_call>

Here are the available tools / actions:

<tools> %s </tools>
Example session:

<question>What is the current price of Solana?</question>
<thought>I need to get the current price of solana</thought>
<tool_call>{"name": "get_actual_data", "arguments": {"moneda": "solana"}, "id": 0}</tool_call>

You will be called again with this:

<observation>{0: {"Precio": "$96,065.33"}}</observation>

You then output:

<response>The current price of Solana is $96,065.33</response>

Example session 2:

<question>What was the price of Ethereum on January 12, 2024?</question>
<thought>I need to get the historical data for ethereum on January 12, 2024</thought>
<tool_call>{"name": "get_historic_data", "arguments": {"moneda": "ethereum", "fecha": "Jan 12, 2024"}, "id": 0}</tool_call>

You will be called again with this:

<observation>{0: {"Apertura": "$189.76", "Alza": "$203.15", "Baja": "$188.48", "MarketCap": "$93,740,476,812"}}</observation>

You then output:

<response>The stock opened at $189.76, reached a high of $203.15, a low of $188.48, and has a market cap of $93.74 billion.</response>

Additional constraints:

- If the user asks you something unrelated to any of the tools above, answer freely enclosing your answer with <response></response> tags.
"""
