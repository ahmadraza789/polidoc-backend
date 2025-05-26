import requests
from .settings import settings
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class Neo4jConnection:
    def __init__(self):
        self.base_url = "https://7035b473.databases.neo4j.io/db/neo4j/query/v2"
        self.auth = (settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Stream": "true"
        }
        logger.info(f"Neo4j HTTP API initialized with URL: {self.base_url}")

    def execute_query(self, query, params=None):
        try:
            # Format query according to Neo4j HTTP API specs
            payload = {
                "statements": [
                    {
                        "statement": query,
                        "parameters": {},
                        "resultDataContents": ["row"],
                        "includeStats": True
                    }
                ]
            }

            logger.info(f"Sending query to Neo4j: {query}")
            logger.info(f"With payload: {payload}")
            
            response = requests.post(
                self.base_url,
                json=payload,
                auth=self.auth,
                headers=self.headers,
                timeout=30
            )

            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response body: {response.text}")

            if response.status_code == 200:
                result = response.json()
                
                # Check for Neo4j errors
                if result.get("errors") and len(result["errors"]) > 0:
                    error = result["errors"][0]
                    error_msg = f"Neo4j query error: {error.get('message', 'Unknown error')}"
                    logger.error(error_msg)
                    raise HTTPException(status_code=400, detail=error_msg)

                # Extract results
                if result.get("results") and len(result["results"]) > 0:
                    first_result = result["results"][0]
                    if "data" not in first_result:
                        return []
                        
                    records = []
                    for item in first_result["data"]:
                        if "row" in item and len(item["row"]) > 0:
                            # Each row is an array of values
                            records.append(item["row"][0])
                    
                    logger.info(f"Query returned {len(records)} records")
                    return records
                return []

            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_msg
                )

        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)

# Create a singleton instance
neo4j_connection = Neo4jConnection()

def get_neo4j_session():
    return neo4j_connection 