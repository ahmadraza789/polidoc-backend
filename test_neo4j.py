from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
neo4j_user = os.getenv('NEO4J_USER')
neo4j_password = os.getenv('NEO4J_PASSWORD')

if not all([neo4j_user, neo4j_password]):
    print("Error: NEO4J_USER and NEO4J_PASSWORD must be set in .env file")
    exit(1)

# Neo4j connection URI - using bolt+ssc:// to allow self-signed certificates
uri = "bolt+ssc://7035b473.databases.neo4j.io:7687"

print("Attempting to connect to Neo4j...")
print(f"URI: {uri}")
print(f"User: {neo4j_user}")

try:
    print("\nCreating driver...")
    driver = GraphDatabase.driver(
        uri,
        auth=(neo4j_user, neo4j_password)
    )
    
    print("Testing connection...")
    driver.verify_connectivity()
    print("✓ Connection verified!")
    
    print("\nTesting queries...")
    with driver.session(database="neo4j") as session:  # Explicitly specify database
        # Test 1: Simple query
        print("\n1. Running simple test query...")
        result = session.run("RETURN 1 as test")
        record = result.single()
        print(f"✓ Simple query result: {record['test']}")
        
        # Test 2: Forms query
        print("\n2. Testing Forms query...")
        result = session.run("MATCH (n:Form) RETURN n LIMIT 1")
        record = result.single()
        if record:
            print("✓ Found a Form node:")
            print(dict(record["n"]))
        else:
            print("✓ Query successful but no Form nodes found")
    
    print("\n✓ All tests completed successfully!")

except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    print("\nPlease check:")
    print("1. Is your Neo4j Aura instance running?")
    print("2. Can you connect via Neo4j Browser?")
    print("3. Are your credentials correct?")
    print("4. Is the database URL correct?")
    
finally:
    if 'driver' in locals():
        driver.close() 