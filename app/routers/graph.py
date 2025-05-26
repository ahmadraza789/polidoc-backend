from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from loguru import logger
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

def get_neo4j_driver():
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        # Test connection
        driver.verify_connectivity()
        return driver
    except Exception as e:
        logger.error(f"Failed to create Neo4j driver: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
        )

def get_neo4j_session():
    driver = get_neo4j_driver()
    try:
        session = driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j"))
        yield session
    finally:
        session.close()
        driver.close()

@router.get("/test-connection")
async def test_connection():
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        driver.close()
        return {"status": "success", "message": "Successfully connected to Neo4j"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to connect to Neo4j: {str(e)}"
        )

@router.get("/forms", response_model=List[Dict[str, Any]])
async def get_forms(neo4j = Depends(get_neo4j_session)):
    try:
        logger.info("Fetching forms from Neo4j...")
        query = """
        MATCH (n:Form)
        WITH n
        RETURN {
            State: n.State,
            Form_Type: n.Form_Type,
            Form_Name: n.Form_Name,
            Form_Number: n.Form_Number
        } as form
        LIMIT 25
        """
        
        result = neo4j.run(query)
        forms = [record["form"] for record in result]
        
        if not forms:
            logger.warning("No forms found in the database")
            return []
            
        logger.info(f"Successfully retrieved {len(forms)} forms")
        return forms
        
    except Exception as e:
        logger.error(f"Failed to fetch forms: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch forms: {str(e)}"
        )

@router.get("/policy-types", response_model=List[Dict[str, Any]])
async def get_policy_types(neo4j = Depends(get_neo4j_session)):
    try:
        logger.info("Fetching policy types from Neo4j...")
        query = """
        MATCH (n) 
        WHERE n.Policy_Type IS NOT NULL
        RETURN DISTINCT "node" as entity, n.Policy_Type AS Policy_Type
        LIMIT 25
        UNION ALL 
        MATCH ()-[r]-() 
        WHERE r.Policy_Type IS NOT NULL
        RETURN DISTINCT "relationship" AS entity, r.Policy_Type AS Policy_Type
        LIMIT 25
        """
        
        result = neo4j.run(query)
        policy_types = [
            {
                "entity": record["entity"],
                "policy_type": record["Policy_Type"]
            } 
            for record in result
        ]
        
        if not policy_types:
            logger.warning("No policy types found in the database")
            return []
            
        logger.info(f"Successfully retrieved {len(policy_types)} policy types")
        return policy_types
        
    except Exception as e:
        logger.error(f"Failed to fetch policy types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch policy types: {str(e)}"
        ) 