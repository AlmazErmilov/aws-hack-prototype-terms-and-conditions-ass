import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from typing import List, Dict, Any, Optional
import os
import re
import time


class VectorDBService:
    def __init__(self, bedrock_service):
        """
        Initialize OpenSearch Serverless client for vector storage
        """
        self.bedrock = bedrock_service
        self.index_name = "tc-chunks"

        # OpenSearch Serverless configuration
        self.collection_endpoint = "mryy2glg64insuvi1bw6.us-west-2.aoss.amazonaws.com"
        self.region = os.environ.get('AWS_DEFAULT_REGION', 'us-west-2')

        # Get AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()

        # Create AWS4Auth for OpenSearch Serverless
        self.auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self.region,
            'aoss',  # Service name for OpenSearch Serverless
            session_token=credentials.token
        )

        # Initialize OpenSearch client
        self.client = OpenSearch(
            hosts=[{'host': self.collection_endpoint, 'port': 443}],
            http_auth=self.auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

        # Ensure index exists
        self._ensure_index()

    def _ensure_index(self):
        """Create the vector index if it doesn't exist"""
        try:
            if not self.client.indices.exists(index=self.index_name):
                # Create index with knn vector mapping
                # Titan embeddings have 1536 dimensions
                index_body = {
                    "settings": {
                        "index": {
                            "knn": True
                        }
                    },
                    "mappings": {
                        "properties": {
                            "embedding": {
                                "type": "knn_vector",
                                "dimension": 1536,
                                "method": {
                                    "name": "hnsw",
                                    "space_type": "cosinesimil",
                                    "engine": "faiss"
                                }
                            },
                            "text": {"type": "text"},
                            "company_id": {"type": "keyword"},
                            "company_name": {"type": "text"},
                            "policy_type": {"type": "keyword"},  # terms, cookie, privacy
                            "chunk_index": {"type": "integer"}
                        }
                    }
                }
                self.client.indices.create(index=self.index_name, body=index_body)
                print(f"Created index: {self.index_name}")
        except Exception as e:
            print(f"Index check/creation error (may be expected): {e}")

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better context retrieval
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to find a sentence break near the end
            if end < len(text):
                # Look for sentence endings
                for sep in ['. ', '.\n', '? ', '?\n', '! ', '!\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start + chunk_size // 2:
                        end = last_sep + 1
                        break

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - overlap
            if start >= len(text):
                break

        return chunks

    def index_policy(self, company_id: str, company_name: str, 
                     policy_text: str, policy_type: str = "terms") -> int:
        """
        Index a company's policy document (terms, cookie, or privacy)
        Returns the number of chunks indexed
        
        Args:
            company_id: Unique identifier for the company
            company_name: Name of the company
            policy_text: The policy text to index
            policy_type: Type of policy - "terms", "cookie", or "privacy"
        """
        # First, remove any existing chunks for this company and policy type
        self.remove_company_policy(company_id, policy_type)

        # Chunk the text
        chunks = self.chunk_text(policy_text)

        if not chunks:
            return 0

        indexed_count = 0

        for i, chunk in enumerate(chunks):
            try:
                embedding = self.bedrock.generate_embedding(chunk)

                doc = {
                    "embedding": embedding,
                    "text": chunk,
                    "company_id": company_id,
                    "company_name": company_name,
                    "policy_type": policy_type,
                    "chunk_index": i
                }

                self.client.index(
                    index=self.index_name,
                    body=doc
                )
                indexed_count += 1

            except Exception as e:
                print(f"Error indexing {policy_type} chunk {i}: {e}")
                continue

        # Refresh index to make documents searchable
        try:
            self.client.indices.refresh(index=self.index_name)
        except Exception as e:
            print(f"Refresh error: {e}")

        return indexed_count

    def index_company_terms(self, company_id: str, company_name: str, terms_text: str) -> int:
        """
        Index a company's terms and conditions (convenience method)
        """
        return self.index_policy(company_id, company_name, terms_text, "terms")

    def index_company_cookie(self, company_id: str, company_name: str, cookie_text: str) -> int:
        """
        Index a company's cookie policy
        """
        return self.index_policy(company_id, company_name, cookie_text, "cookie")

    def index_company_privacy(self, company_id: str, company_name: str, privacy_text: str) -> int:
        """
        Index a company's privacy policy
        """
        return self.index_policy(company_id, company_name, privacy_text, "privacy")

    def remove_company_policy(self, company_id: str, policy_type: str):
        """
        Remove all chunks for a company's specific policy type
        """
        try:
            self.client.delete_by_query(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"company_id": company_id}},
                                {"term": {"policy_type": policy_type}}
                            ]
                        }
                    }
                }
            )
        except Exception as e:
            print(f"Error removing {policy_type} for company {company_id}: {e}")

    def remove_company(self, company_id: str):
        """
        Remove all chunks for a company (all policy types)
        """
        try:
            # Delete by query
            self.client.delete_by_query(
                index=self.index_name,
                body={
                    "query": {
                        "term": {
                            "company_id": company_id
                        }
                    }
                }
            )
        except Exception as e:
            print(f"Error removing company {company_id}: {e}")

    def search(self, query: str, n_results: int = 5,
               company_id: Optional[str] = None,
               policy_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks based on query using kNN
        
        Args:
            query: The search query
            n_results: Number of results to return
            company_id: Optional filter by company
            policy_type: Optional filter by policy type (terms, cookie, privacy)
        """
        try:
            # Generate embedding for query
            query_embedding = self.bedrock.generate_embedding(query)

            # Build kNN query
            knn_query = {
                "knn": {
                    "embedding": {
                        "vector": query_embedding,
                        "k": n_results
                    }
                }
            }

            # Build filters
            filters = []
            if company_id:
                filters.append({"term": {"company_id": company_id}})
            if policy_type:
                filters.append({"term": {"policy_type": policy_type}})

            # Add filters if any specified
            if filters:
                search_body = {
                    "size": n_results,
                    "query": {
                        "bool": {
                            "must": [knn_query],
                            "filter": filters
                        }
                    }
                }
            else:
                search_body = {
                    "size": n_results,
                    "query": knn_query
                }

            # Execute search
            response = self.client.search(
                index=self.index_name,
                body=search_body
            )

            # Format results
            formatted = []
            for hit in response['hits']['hits']:
                source = hit['_source']
                formatted.append({
                    "text": source.get('text'),
                    "company_id": source.get('company_id'),
                    "company_name": source.get('company_name'),
                    "policy_type": source.get('policy_type', 'terms'),
                    "chunk_index": source.get('chunk_index'),
                    "score": hit.get('_score')
                })

            return formatted

        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database including breakdown by policy type
        """
        try:
            # Get total count
            count_response = self.client.count(index=self.index_name)
            total = count_response.get('count', 0)
            
            # Get breakdown by policy type using aggregation
            agg_body = {
                "size": 0,
                "aggs": {
                    "by_policy_type": {
                        "terms": {
                            "field": "policy_type",
                            "size": 10
                        }
                    },
                    "by_company": {
                        "cardinality": {
                            "field": "company_id"
                        }
                    }
                }
            }
            
            agg_response = self.client.search(index=self.index_name, body=agg_body)
            
            # Parse aggregation results
            policy_counts = {}
            buckets = agg_response.get('aggregations', {}).get('by_policy_type', {}).get('buckets', [])
            for bucket in buckets:
                policy_counts[bucket['key']] = bucket['doc_count']
            
            company_count = agg_response.get('aggregations', {}).get('by_company', {}).get('value', 0)
            
            return {
                "total_chunks": total,
                "chunks_by_policy_type": {
                    "terms": policy_counts.get('terms', 0),
                    "cookie": policy_counts.get('cookie', 0),
                    "privacy": policy_counts.get('privacy', 0)
                },
                "unique_companies": company_count,
                "index_name": self.index_name,
                "collection_endpoint": self.collection_endpoint
            }
        except Exception as e:
            return {
                "total_chunks": 0,
                "chunks_by_policy_type": {"terms": 0, "cookie": 0, "privacy": 0},
                "unique_companies": 0,
                "index_name": self.index_name,
                "collection_endpoint": self.collection_endpoint,
                "error": str(e)
            }
