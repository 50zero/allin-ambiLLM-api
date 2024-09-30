from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError
import time
import logging
import json
from config import Config
from utils import setup_logging, parse_assistant_response
import os
from typing import Any, List, Union

api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI(api_key=api_key)

app = Flask(__name__)
logger = setup_logging()

class ValidationRequest(BaseModel):
    market_description: str
    market_question: str
    resolution_date: str

class DescriptionRequest(BaseModel):
    question: str

class SuggestionRequest(BaseModel):
    question: str
    description: str

class MessageContent(BaseModel):
    content: Any

    class Config:
        arbitrary_types_allowed = True

def validate_market_logic(market_description, market_question, resolution_date):
    try:
        validation_assistant = client.beta.assistants.retrieve(Config.VALIDATION_ASSISTANT_ID)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Market Question: {market_question}\nMarket Description: {market_description}\nResolution Date: {resolution_date}",
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=validation_assistant.id
        )

        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            logger.info(f"Validation Run status: {run.status}")

        all_messages = client.beta.threads.messages.list(thread_id=thread.id)
        
        parsed_response = parse_assistant_response(all_messages)

        if not parsed_response:
            logger.error(f"No valid JSON object found in the response. Response received: {all_messages.data}")
            return {'error': 'No valid JSON object found in the response.'}, 500

        return parsed_response, 200

    except OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return {'error': 'OpenAI error occurred. Please try again later.'}, 500
    except Exception as e:
        logger.error(f"Error processing the request: {str(e)}")
        return {'error': 'Failed to validate the market. Please try again later.'}, 500

def generate_description_logic(question):
    try:
        description_assistant = client.beta.assistants.retrieve(Config.DESCRIPTION_ASSISTANT_ID)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Here is the question: {question}",
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=description_assistant.id
        )

        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            logger.info(f"Run status: {run.status}")

        all_messages = client.beta.threads.messages.list(thread_id=thread.id)

        generated_text = ""
        for message in all_messages.data:
            try:
                for block in message.content:
                    generated_text += block.text.value + " "
            except Exception as e:
                logger.error(f"Failed to extract text content: {str(e)}")

        # JSON Conversion
        json_assistant = client.beta.assistants.retrieve(Config.JSON_ASSISTANT_ID)

        json_thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=json_thread.id,
            role="user",
            content=f"Convert the following text into a valid JSON object: {generated_text}",
        )

        json_run = client.beta.threads.runs.create(
            thread_id=json_thread.id,
            assistant_id=json_assistant.id
        )

        while json_run.status != "completed":
            time.sleep(1)
            json_run = client.beta.threads.runs.retrieve(
                thread_id=json_thread.id,
                run_id=json_run.id
            )
            logger.info(f"JSON Run status: {json_run.status}")

        json_messages = client.beta.threads.messages.list(thread_id=json_thread.id)

        parsed_response = parse_assistant_response(json_messages)

        return parsed_response, 200

    except OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return {'error': 'OpenAI error occurred. Please try again later.'}, 500
    except Exception as e:
        logger.error(f"Error processing the request: {str(e)}")
        return {'error': 'Failed to generate a description. Please try again later.'}, 500

def generate_suggestions_logic(question, mkt_description):
    try:
        suggestion_assistant = client.beta.assistants.retrieve(Config.SUGGESTION_ASSISTANT_ID)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Here is the question: {question}"
        )

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Here is the market description: {mkt_description}"
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=suggestion_assistant.id
        )

        while run.status != "completed":
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            logger.info(f"Suggestion Run status: {run.status}")

        all_messages = client.beta.threads.messages.list(thread_id=thread.id)

        response_content = []
        for message in all_messages.data:
            if message.role == 'assistant':
                try:
                    for content in message.content:
                        if hasattr(content, 'text') and hasattr(content.text, 'value'):
                            response_content.append(content.text.value)
                except Exception as e:
                    logger.error(f"Failed to process message content: {str(e)}")

        return {'response': response_content}, 200

    except OpenAIError as e:
        logger.error(f"OpenAI error: {str(e)}")
        return {'error': 'OpenAI error occurred. Please try again later.'}, 500
    except Exception as e:
        logger.error(f"Error processing the request: {str(e)}")
        return {'error': 'Failed to generate suggestions. Please try again later.'}, 500


@app.route('/api/validate-market', methods=['POST'])
def validate_market_flask():
    try:
        data = request.json
        validation_request = ValidationRequest(**data)
        result, status_code = validate_market_logic(
            validation_request.market_description, 
            validation_request.market_question,
            validation_request.resolution_date
        )
        return jsonify(result), status_code
    except ValidationError as e:
        return jsonify({'error': 'Invalid input', 'details': str(e)}), 400

@app.route('/api/generate-description', methods=['POST'])
def generate_description_flask():
    try:
        data = request.json
        description_request = DescriptionRequest(**data)
        result, status_code = generate_description_logic(description_request.question)
        return jsonify(result), status_code
    except ValidationError as e:
        return jsonify({'error': 'Invalid input', 'details': str(e)}), 400

@app.route('/api/generate-suggestions', methods=['POST'])
def generate_suggestions_flask():
    try:
        data = request.json
        suggestion_request = SuggestionRequest(**data)
        result, status_code = generate_suggestions_logic(
            suggestion_request.question,
            suggestion_request.description
        )
        return jsonify(result), status_code
    except ValidationError as e:
        return jsonify({'error': 'Invalid input', 'details': str(e)}), 400

def validate_market(event, context):
    try:
        body = json.loads(event['body'])
        validation_request = ValidationRequest(**body)
        result, status_code = validate_market_logic(
            validation_request.market_description, 
            validation_request.market_question,
            validation_request.resolution_date
        )
        return {
            'statusCode': status_code,
            'body': json.dumps(result)
        }
    except (json.JSONDecodeError, ValidationError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid input', 'details': str(e)})
        }

def generate_description(event, context):
    try:
        body = json.loads(event['body'])
        description_request = DescriptionRequest(**body)
        result, status_code = generate_description_logic(description_request.question)
        return {
            'statusCode': status_code,
            'body': json.dumps(result)
        }
    except (json.JSONDecodeError, ValidationError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid input', 'details': str(e)})
        }

def generate_suggestions(event, context):
    try:
        body = json.loads(event['body'])
        suggestion_request = SuggestionRequest(**body)
        result, status_code = generate_suggestions_logic(
            suggestion_request.question,
            suggestion_request.description
        )
        return {
            'statusCode': status_code,
            'body': json.dumps(result)
        }
    except (json.JSONDecodeError, ValidationError) as e:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Invalid input', 'details': str(e)})
        }

def create_app():
    return app
