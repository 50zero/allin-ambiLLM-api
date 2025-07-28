# allin-ambiLLM-api

A serverless API built with AWS SAM (Serverless Application Model) that provides AI-powered market validation and content generation services using OpenAI's GPT models.

## Features

- **Market Validation** (`/api/validate-market`) - Validates market opportunities and business ideas
- **Description Generation** (`/api/generate-description`) - Generates detailed descriptions for questions or concepts  
- **Suggestion Generation** (`/api/generate-suggestions`) - Provides AI-powered suggestions and recommendations

## Tech Stack

- **AWS Lambda** - Serverless compute functions
- **API Gateway** - REST API endpoints
- **Python 3.10** - Runtime environment
- **OpenAI GPT** - AI language model integration
- **AWS SAM** - Infrastructure as Code

## API Endpoints

All endpoints accept POST requests and return JSON responses.

- `POST /api/validate-market` - Market validation analysis
- `POST /api/generate-description` - Content description generation
- `POST /api/generate-suggestions` - AI-powered suggestions

## Deployment

This project uses AWS SAM for deployment. Ensure you have AWS CLI configured and SAM CLI installed.

```bash
sam build
sam deploy --guided
```

## Environment Variables

- `OPENAI_API_KEY` - Your OpenAI API key (required)
