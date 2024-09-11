from flask import Flask, request, jsonify
from openai import OpenAI, OpenAIError
from pydantic import BaseModel, ValidationError
import time
import logging
import json
from config import Config
from utils import setup_logging, parse_assistant_response
import os

api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

client = OpenAI(api_key=api_key)

app = Flask(__name__)
logger = setup_logging()

class ValidationRequest(BaseModel):
    market_description: str
    market_question: str

def validate_market_logic(market_description, market_question):
    try:
        validation_assistant = client.beta.assistants.retrieve(Config.ASSISTANT_ID)

        thread = client.beta.threads.create()

        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Market Question: {market_question}\nMarket Description: {market_description}",
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

@app.route('/api/validate-market', methods=['POST'])
def validate_market_flask():
    try:
        data = request.json
        validation_request = ValidationRequest(**data)
        result, status_code = validate_market_logic(validation_request.market_description, validation_request.market_question)
        return jsonify(result), status_code
    except ValidationError as e:
        return jsonify({'error': 'Invalid input', 'details': str(e)}), 400

def validate_market(event, context):
    try:
        body = json.loads(event['body'])
        validation_request = ValidationRequest(**body)
        result, status_code = validate_market_logic(validation_request.market_description, validation_request.market_question)
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
