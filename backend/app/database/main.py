import uuid
from datetime import datetime
from neo4j import GraphDatabase
from app.config import settings

# Neo4j connection
NEO4J_URL = settings.NEO4J_URL
if not NEO4J_URL:
    raise ValueError("NEO4J_URL must be set in environment variables.")
NEO4J_USER = settings.NEO4J_USER
if not NEO4J_USER:
    raise ValueError("NEO4J_USER must be set in environment variables.")
NEO4J_PASSWORD = settings.NEO4J_PASSWORD
if not NEO4J_PASSWORD:
    raise ValueError("NEO4J_PASSWORD must be set in environment variables.")

def check_neo4j_connection():
    try:
        with GraphDatabase.driver(
            NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD)
        ) as driver:
            driver.verify_connectivity()
        return True
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return False

def execute_neo4j_query(query, parameters=None) -> list | None:
    with GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD)) as driver:
        try:
            records, _, _ = driver.execute_query(query, parameters_=parameters)
            return [record.data() for record in records]
        except Exception as e:
            print(f"Error executing Neo4j query: {e}")
            return None

def generate_id() -> str:
    """Generate a unique ID for a new document."""
    return str(uuid.uuid4())

def get_current_timestamp() -> str:
    """Get the current timestamp."""
    return datetime.now().isoformat()
