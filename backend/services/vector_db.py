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

    def index_company_terms(self, company_id: str, company_name: str, terms_text: str) -> int:
        """
        Index a company's terms and conditions
        Returns the number of chunks indexed
        """
        # First, remove any existing chunks for this company
        self.remove_company(company_id)

        # Chunk the text
        chunks = self.chunk_text(terms_text)

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
                    "chunk_index": i
                }

                self.client.index(
                    index=self.index_name,
                    body=doc
                )
                indexed_count += 1

            except Exception as e:
                print(f"Error indexing chunk {i}: {e}")
                continue

        # Refresh index to make documents searchable
        try:
            self.client.indices.refresh(index=self.index_name)
        except Exception as e:
            print(f"Refresh error: {e}")

        return indexed_count

    def remove_company(self, company_id: str):
        """
        Remove all chunks for a company
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
               company_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks based on query using kNN
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

            # Add filter if company_id specified
            if company_id:
                search_body = {
                    "size": n_results,
                    "query": {
                        "bool": {
                            "must": [knn_query],
                            "filter": [
                                {"term": {"company_id": company_id}}
                            ]
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
                    "chunk_index": source.get('chunk_index'),
                    "score": hit.get('_score')
                })

            return formatted

        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database
        """
        try:
            count_response = self.client.count(index=self.index_name)
            return {
                "total_chunks": count_response.get('count', 0),
                "index_name": self.index_name,
                "collection_endpoint": self.collection_endpoint
            }
        except Exception as e:
            return {
                "total_chunks": 0,
                "index_name": self.index_name,
                "collection_endpoint": self.collection_endpoint,
                "error": str(e)
            }
