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

    def analyze_cookie_policy(self, company_name: str, cookie_text: str) -> Dict[str, Any]:
        """
        Analyze cookie policy using Claude Sonnet 4 on Bedrock
        Returns a summary and list of cookie-related risks
        """
        prompt = f"""You are an expert privacy analyst specializing in cookie policies. Analyze the following Cookie Policy for {company_name}.

Provide your analysis in the following JSON format:
{{
    "cookie_summary": "A brief 2-3 sentence summary of the cookie practices",
    "cookie_risks": [
        {{
            "title": "Risk title",
            "description": "Detailed description of the cookie-related risk",
            "severity": "low|medium|high"
        }}
    ]
}}

Focus on:
1. Types of cookies used (essential, functional, analytics, advertising)
2. Third-party cookies and trackers
3. Cookie duration and persistence
4. Cross-site tracking capabilities
5. User consent mechanisms
6. Opt-out options and their effectiveness
7. Data collected through cookies
8. Cookie sharing with third parties

Cookie Policy:
{cookie_text[:8000]}

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
                "cookie_summary": "Unable to parse cookie analysis",
                "cookie_risks": [
                    {
                        "title": "Analysis Error",
                        "description": result_text[:500],
                        "severity": "medium"
                    }
                ]
            }

    def analyze_privacy_policy(self, company_name: str, privacy_text: str) -> Dict[str, Any]:
        """
        Analyze privacy policy using Claude Sonnet 4 on Bedrock
        Returns a summary and list of privacy-related risks
        """
        prompt = f"""You are an expert privacy analyst specializing in privacy policies. Analyze the following Privacy Policy for {company_name}.

Provide your analysis in the following JSON format:
{{
    "privacy_summary": "A brief 2-3 sentence summary of the privacy practices",
    "privacy_risks": [
        {{
            "title": "Risk title",
            "description": "Detailed description of the privacy-related risk",
            "severity": "low|medium|high"
        }}
    ]
}}

Focus on:
1. Types of personal data collected (PII, sensitive data, biometrics)
2. Data retention periods and policies
3. Third-party data sharing and selling
4. User rights (access, deletion, portability)
5. Data security measures mentioned
6. International data transfers
7. Children's privacy protections
8. Automated decision-making and profiling

Privacy Policy:
{privacy_text[:8000]}

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
                "privacy_summary": "Unable to parse privacy analysis",
                "privacy_risks": [
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

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings using Amazon Titan Embeddings model
        """
        # Truncate text if too long (Titan has 8k token limit)
        text = text[:8000]

        body = json.dumps({
            "inputText": text
        })

        response = self.client.invoke_model(
            modelId="amazon.titan-embed-text-v1",
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body['embedding']

    def rag_chat(self, user_question: str, context_chunks: List[Dict[str, Any]],
                 conversation_history: List[Dict[str, str]] = None) -> str:
        """
        Answer user questions using RAG with retrieved context
        """
        # Build context from retrieved chunks
        context_text = ""
        policy_type_labels = {
            "terms": "Terms & Conditions",
            "cookie": "Cookie Policy",
            "privacy": "Privacy Policy"
        }
        
        for i, chunk in enumerate(context_chunks, 1):
            company = chunk.get('company_name', 'Unknown')
            policy_type = chunk.get('policy_type', 'terms')
            policy_label = policy_type_labels.get(policy_type, 'Terms & Conditions')
            text = chunk.get('text', '')
            context_text += f"\n[Source {i} - {company} ({policy_label})]:\n{text}\n"

        # Build conversation history
        messages = []
        if conversation_history:
            for msg in conversation_history[-6:]:  # Keep last 6 messages for context
                messages.append({"role": msg["role"], "content": msg["content"]})

        system_prompt = """You are a helpful assistant that explains Terms and Conditions, Cookie Policies, and Privacy Policies in simple, clear language.
You have access to excerpts from various companies' legal documents including terms of service, cookie policies, and privacy policies.
Always cite which company and document type you're referencing in your answers.
If the retrieved context doesn't contain relevant information, say so honestly.
Be concise but thorough in your explanations."""

        user_prompt = f"""Based on the following excerpts from company policies:
{context_text}

User question: {user_question}

Please provide a clear, helpful answer based on the context above."""

        messages.append({"role": "user", "content": user_prompt})

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "temperature": 0.5,
            "top_p": 0.9,
            "system": system_prompt,
            "messages": messages
        })

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']
