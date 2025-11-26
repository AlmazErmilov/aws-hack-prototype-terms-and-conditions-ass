import boto3
import json
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class BedrockService:
    def __init__(self):
        self.client = boto3.client(
            'bedrock-runtime',
            region_name='us-west-2',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        # Use cross-region inference profile for Claude Sonnet 4
        self.model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    def analyze_terms_and_conditions(self, company_name: str, terms_text: str) -> Dict[str, Any]:
        """
        Analyze terms and conditions using Claude Sonnet 4 on Bedrock
        Returns a summary and list of risks
        """
        prompt = f"""You are an expert privacy analyst. Analyze the following Terms and Conditions for {company_name}.

Provide your analysis in the following JSON format:
{{
    "summary": "A brief 2-3 sentence summary of what users agree to",
    "risks": [
        {{
            "title": "Risk title",
            "description": "Detailed description of the risk",
            "severity": "low|medium|high"
        }}
    ]
}}

Focus on:
1. Data collection practices
2. Data sharing with third parties
3. User tracking and profiling
4. Content ownership and licensing
5. Account termination policies
6. Arbitration clauses
7. Privacy concerns
8. Financial implications

Terms and Conditions:
{terms_text[:8000]}

Respond ONLY with valid JSON, no additional text."""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": 0.3,
            "top_p": 0.9,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        result_text = response_body['content'][0]['text']

        # Parse the JSON response
        try:
            # Clean up response if needed
            result_text = result_text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            # Find JSON in response
            start_idx = result_text.find('{')
            end_idx = result_text.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                result_text = result_text[start_idx:end_idx]

            analysis = json.loads(result_text.strip())
            return analysis
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "summary": "Unable to parse analysis",
                "risks": [
                    {
                        "title": "Analysis Error",
                        "description": result_text[:500],
                        "severity": "medium"
                    }
                ]
            }

    def chat_about_terms(self, company_name: str, terms_text: str, user_question: str) -> str:
        """
        Answer user questions about specific terms and conditions
        """
        prompt = f"""You are a helpful assistant that explains Terms and Conditions in simple language.

Company: {company_name}

Terms and Conditions excerpt:
{terms_text[:6000]}

User question: {user_question}

Provide a clear, concise answer. If the terms don't address this question, say so."""

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,
            "temperature": 0.5,
            "top_p": 0.9,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
