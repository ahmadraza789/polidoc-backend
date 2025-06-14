from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from loguru import logger
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from pydantic import BaseModel

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

class QueryRequest(BaseModel):
    terms: List[str]
    policy_form: str = "HO00030511"
    manually_selected_paragraphs: Optional[List[int]] = None

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

@router.get("/coverages", response_model=List[Dict[str, Any]])
async def get_coverages(neo4j = Depends(get_neo4j_session)):
    try:
        logger.info("Fetching coverages from Neo4j...")
        query = """
        MATCH (n:Coverage) 
        RETURN n
        LIMIT 25
        """
        
        result = neo4j.run(query)
        coverages = [dict(record["n"]) for record in result]
        
        if not coverages:
            logger.warning("No coverages found in the database")
            return []
            
        logger.info(f"Successfully retrieved {len(coverages)} coverages")
        return coverages
        
    except Exception as e:
        logger.error(f"Failed to fetch coverages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch coverages: {str(e)}"
        )

@router.get("/form-policy-type/{form_number}", response_model=Dict[str, str])
async def get_policy_type_by_form(form_number: str, neo4j = Depends(get_neo4j_session)):
    try:
        logger.info(f"Fetching policy type for form number: {form_number}")
        query = """
        MATCH (f:Form)
        WHERE f.Form_Number = $form_number
        RETURN f.Form_Type as policy_type
        """
        
        result = neo4j.run(query, form_number=form_number)
        record = result.single()
        
        if not record:
            logger.warning(f"No form found with form number: {form_number}")
            raise HTTPException(
                status_code=404,
                detail=f"Form not found with form number: {form_number}"
            )
            
        policy_type = record["policy_type"]
        logger.info(f"Successfully retrieved policy type: {policy_type}")
        return {"policy_type": policy_type}
        
    except Exception as e:
        logger.error(f"Failed to fetch policy type for form {form_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch policy type: {str(e)}"
        )

@router.get("/form-coverages/{form_number}", response_model=List[Dict[str, str]])
async def get_coverages_by_form(form_number: str, neo4j = Depends(get_neo4j_session)):
    try:
        logger.info(f"Fetching coverages for form number: {form_number}")
        query = """
        MATCH(p:Paragraph)-[y:Related_Coverage]-(c:Coverage)
        WHERE p.Policy_Form = $form_number
        RETURN DISTINCT c.Coverage as coverage_code, c.Cov_For as coverage_name
        ORDER BY c.Coverage
        """
        
        result = neo4j.run(query, form_number=form_number)
        coverages = [
            {
                "coverage_code": record["coverage_code"],
                "coverage_name": record["coverage_name"]
            }
            for record in result
        ]
        
        if not coverages:
            logger.warning(f"No coverages found for form number: {form_number}")
            return []
            
        logger.info(f"Successfully retrieved {len(coverages)} coverages for form {form_number}")
        return coverages
        
    except Exception as e:
        logger.error(f"Failed to fetch coverages for form {form_number}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch coverages: {str(e)}"
        )

@router.get("/form-coverage-terms/{form_number}/{coverage_code}", response_model=List[Dict[str, str]])
async def get_coverage_terms(
    form_number: str,
    coverage_code: str,
    neo4j = Depends(get_neo4j_session)
):
    try:
        logger.info(f"Fetching terms for form {form_number} and coverage {coverage_code}")
        query = """
        MATCH (m:Map_Term)-[x:Maps_To]-(p:Paragraph)-[y:Related_Coverage]-(c:Coverage)
        WHERE p.Policy_Form = $form_number 
        AND x.Map_Type <> 'None' 
        AND c.Coverage = $coverage_code
        AND p.Type <> 'Section Title'
        AND p.Type <> 'Subsection Title'
        RETURN DISTINCT c.Coverage as coverage_code, 
                        x.Map_Type as map_type,
                        m.Term as term
        ORDER BY c.Coverage, x.Map_Type, m.Term
        """
        
        result = neo4j.run(query, form_number=form_number, coverage_code=coverage_code)
        terms = [
            {
                "coverage_code": record["coverage_code"],
                "map_type": record["map_type"],
                "term": record["term"]
            }
            for record in result
        ]
        
        if not terms:
            logger.warning(f"No terms found for form {form_number} and coverage {coverage_code}")
            return []
            
        logger.info(f"Successfully retrieved {len(terms)} terms for form {form_number} and coverage {coverage_code}")
        return terms
        
    except Exception as e:
        logger.error(f"Failed to fetch terms for form {form_number} and coverage {coverage_code}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch coverage terms: {str(e)}"
        )

@router.get("/ccq-list", response_model=Dict[str, List[str]])
async def get_ccq_list(
    policy_form: str = "HO00030511",
    neo4j = Depends(get_neo4j_session)
):
    try:
        logger.info(f"Fetching CCQ list for policy form: {policy_form}")
        query = """
        MATCH (p:Paragraph)-[r:Maps_To]->(m:Map_Term)
        WHERE r.Map_Type IN ['Non-Covered Peril','Limit of Liability','Property Not Covered'] 
        AND p.Policy_Form = $policy_form
        RETURN DISTINCT r.Map_Type as mapType, m.Term AS term
        ORDER BY term
        """
        
        result = neo4j.run(query, policy_form=policy_form)
        
        # Build a grouped object, with keys as map types and values as arrays of terms
        groups = {}
        for record in result:
            map_type = record["mapType"]
            term = record["term"]
            if map_type not in groups:
                groups[map_type] = []
            groups[map_type].append(term)
            
        logger.info(f"Successfully retrieved CCQ list with {len(groups)} map types")
        return groups
        
    except Exception as e:
        logger.error(f"Failed to fetch CCQ list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch CCQ list: {str(e)}"
        )

@router.get("/all-paragraphs", response_model=List[Dict[str, Any]])
async def get_all_paragraphs(
    policy_form: str = "HO00030511",
    neo4j = Depends(get_neo4j_session)
):
    try:
        logger.info(f"Fetching all paragraphs for policy form: {policy_form}")
        query = """
        MATCH (p:Paragraph)
        WHERE p.Policy_Form = $policy_form
        RETURN p.Paragraph_Number AS ParagraphNumber,
               p.Section AS Section,
               p.Subsection AS Subsection,
               p.Text AS Text,
               p.Page AS Page
        ORDER BY p.Paragraph_Number
        """
        
        result = neo4j.run(query, policy_form=policy_form)
        paragraphs = [
            {
                "ParagraphNumber": record["ParagraphNumber"],
                "Section": record["Section"],
                "Subsection": record["Subsection"],
                "Text": record["Text"],
                "Page": record["Page"]
            }
            for record in result
        ]
        
        logger.info(f"Successfully retrieved {len(paragraphs)} paragraphs")
        return paragraphs
        
    except Exception as e:
        logger.error(f"Failed to fetch all paragraphs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch all paragraphs: {str(e)}"
        )

@router.post("/query", response_model=List[Dict[str, Any]])
async def query_paragraphs(
    request: QueryRequest,
    neo4j = Depends(get_neo4j_session)
):
    try:
        logger.info(f"Querying paragraphs for terms: {request.terms} in policy form: {request.policy_form}")
        # Convert paragraph numbers to strings if they exist
        paragraph_numbers = [str(num) for num in (request.manually_selected_paragraphs or [])]
        
        query = """
        MATCH (p:Paragraph)
        WHERE p.Policy_Form = $policy_form 
        AND (
            (EXISTS((p)-[:Maps_To]->(:Map_Term)) AND ANY(term IN $terms WHERE EXISTS((p)-[:Maps_To]->(:Map_Term {Term: term}))))
            OR p.Type = 'Policy Title Section'
            OR toString(p.Paragraph_Number) IN $manually_selected_paragraphs
        )
        RETURN DISTINCT p.Section AS Section,
               p.Subsection AS Subsection,
               p.List_Item AS ListItem,
               p.Type AS Type,
               p.Paragraph_Number AS ParagraphNumber,
               p.Page AS Page,
               p.Text AS Text
        ORDER BY p.Paragraph_Number
        """
        
        result = neo4j.run(
            query,
            policy_form=request.policy_form,
            terms=request.terms,
            manually_selected_paragraphs=paragraph_numbers
        )
        
        paragraphs = [
            {
                "Section": record["Section"],
                "Subsection": record["Subsection"],
                "ListItem": record["ListItem"],
                "Type": record["Type"],
                "ParagraphNumber": record["ParagraphNumber"],
                "Page": record["Page"],
                "Text": record["Text"]
            }
            for record in result
        ]
        
        logger.info(f"Successfully retrieved {len(paragraphs)} paragraphs for query")
        return paragraphs
        
    except Exception as e:
        logger.error(f"Failed to execute query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute query: {str(e)}"
        ) 