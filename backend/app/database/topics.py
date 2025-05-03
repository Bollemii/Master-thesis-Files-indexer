import json

from app.database.main import execute_neo4j_query, generate_id
from app.database.models import Topic


def get_all_topics() -> list[Topic]:
    """Get all topics from the database."""
    result = execute_neo4j_query("MATCH (t:Topic) RETURN t;")
    return [
        Topic(
            identifier=topic["t"]["id"],
            name=topic["t"]["name"],
            words=json.loads(topic["t"]["words"]),
            description=topic["t"].get("description"),
        )
        for topic in result
    ] if result else []

def get_topic_by_id(topic_id: str) -> Topic | None:
    """Get a topic by its identifier."""
    if not topic_id:
        raise ValueError("Topic identifier is required.")

    result = execute_neo4j_query(
        "MATCH (t:Topic {id: $id}) RETURN t;",
        parameters={"id": topic_id},
    )
    if result:
        topic = result[0]["t"]
        return Topic(
            identifier=topic["id"],
            name=topic["name"],
            words=json.loads(topic["words"]),
            description=topic.get("description"),
        )
    return None

def get_topic_by_name(name: str) -> Topic | None:
    """Get a topic by its name."""
    if not name:
        raise ValueError("Topic name is required.")

    result = execute_neo4j_query(
        "MATCH (t:Topic {name: $name}) RETURN t;",
        parameters={"name": name},
    )
    if result:
        topic = result[0]["t"]
        return Topic(
            identifier=topic["id"],
            name=topic["name"],
            words=json.loads(topic["words"]),
            description=topic.get("description"),
        )
    return None

def create_topic(name: str, words: dict[str, float], description: str | None = None) -> Topic:
    """Create a new topic in the database."""
    if not name:
        raise ValueError("Topic name is required.")
    if not words:
        raise ValueError("Topic words are required.")

    topics = get_all_topics()
    if any(topic.name == name for topic in topics):
        raise ValueError("Topic with this name already exists.")

    identifier = generate_id()
    execute_neo4j_query(
        """CREATE (t:Topic {id: $id, name: $name, words: $words, description: $description})""",
        parameters={
            "id": identifier,
            "name": name,
            "words": json.dumps(words),
            "description": description
        },
    )
    return Topic(identifier, name, words, description)

def update_topic(topic_id: str, name: str | None = None, words: dict[str, float] | None = None, description: str | None = None) -> Topic:
    """Update an existing topic in the database."""
    if not topic_id:
        raise ValueError("Topic identifier is required.")

    topic = get_topic_by_id(topic_id)
    if topic is None:
        print(f"Topic with ID {topic_id} not found.")
        raise ValueError("Topic not found.")

    if name:
        topic.name = name
    if words:
        topic.words = words
    if description:
        topic.description = description

    execute_neo4j_query(
        """MATCH (t:Topic {id: $id}) SET t.name = $name, t.words = $words, t.description = $description""",
        parameters={
            "id": topic_id,
            "name": topic.name,
            "words": json.dumps(topic.words),
            "description": topic.description,
        },
    )
    return topic

def delete_topic(topic_id: str) -> None:
    """Delete a topic from the database."""
    if not topic_id:
        raise ValueError("Topic identifier is required.")

    execute_neo4j_query(
        """MATCH (t:Topic {id: $id}) DETACH DELETE t""",
        parameters={"id": topic_id},
    )
