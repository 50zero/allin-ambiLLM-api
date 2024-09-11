import logging
import json

def setup_logging():
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)

def parse_assistant_response(all_messages):
    parsed_response = {}
    for message in all_messages.data:
        if message.role == 'assistant':
            try:
                content_str = message.content[0].text.value
                try:
                    content_json = json.loads(content_str)
                    parsed_response.update(content_json)
                except json.JSONDecodeError:
                    logging.warning("Failed to parse JSON from message content.")
            except (IndexError, AttributeError):
                logging.warning("Unexpected message content structure.")
    return parsed_response
