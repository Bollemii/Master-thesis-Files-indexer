from passlib.context import CryptContext
from app.database.main import execute_neo4j_query, generate_id, get_current_timestamp
from app.database.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_all_users() -> list[User]:
    """Get all users from the database"""
    result = execute_neo4j_query("MATCH (u:User) RETURN u;")
    return [
        User(
            identifier=user["u"]["id"],
            username=user["u"]["username"],
            hashed_password=user["u"]["hashed_password"],
            is_superuser=user["u"]["is_superuser"],
            creation_date=user["u"]["creation_date"],
        )
        for user in result
    ] if result else []

def get_user_by_username(username: str) -> User | None:
    """Get a user by their username"""
    if not username:
        raise ValueError("Username must be provided.")
    result = execute_neo4j_query(
        "MATCH (u:User {username: $username}) RETURN u;",
        parameters={"username": username},
    )
    return User(
        identifier=result[0]["u"]["id"],
        username=result[0]["u"]["username"],
        hashed_password=result[0]["u"]["hashed_password"],
        is_superuser=result[0]["u"]["is_superuser"],
        creation_date=result[0]["u"]["creation_date"],
    ) if result else None

def create_user(username: str, password: str, is_superuser: bool = False) -> User:
    """Create a new user in the database"""
    if not username or not password:
        raise ValueError("Username and password are required")

    users = get_all_users()
    if any(user["username"] == username for user in users):
        raise ValueError("Username already exists")

    identifier = generate_id()
    hashed_password = pwd_context.hash(password)
    creation_date = get_current_timestamp()
    execute_neo4j_query(
        """CREATE (u:User {id: $id, username: $username, hashed_password: $hashed_password, is_superuser: $is_superuser, creation_date: $creation_date});""",
        parameters={
            "id": identifier,
            "username": username,
            "hashed_password": hashed_password,
            "is_superuser": is_superuser,
            "is_active": True,
            "creation_date": creation_date,
        },
    )
    return User(identifier, username, hashed_password, is_superuser, creation_date)
