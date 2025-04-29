class Document:
    """Class representing a document in the database."""

    def __init__(
        self,
        identifier: str,
        filename: str,
        path: str,
        processed: bool = False,
        upload_date: str | None = None,
    ):
        self.id = identifier
        self.filename = filename
        self.path = path
        self.processed = processed
        self.upload_date = upload_date

    def __repr__(self):
        return f"Document(id={self.id}, filename={self.filename}, path={self.path}, processed={self.processed}, upload_date={self.upload_date})"


class Chunk:
    """Class representing a chunk of a document in the database."""

    def __init__(
        self,
        identifier: str,
        text: str,
        embedding: list[float],
        document_id: str | None = None,
        document_name: str | None = None,
        document_path: str | None = None,
        document_processed: bool | None = None,
        document_upload_date: str | None = None,
    ):
        self.id = identifier
        self.text = text
        self.embedding = embedding if embedding is not None else []
        self.document = (
            Document(
                document_id,
                document_name,
                document_path,
                document_processed,
                document_upload_date,
            )
            if document_id
            else None
        )

    def __repr__(self):
        return f"Chunk(id={self.id}, document_id={self.document.id})"


class Topic:
    """Class representing a topic in the database."""

    def __init__(
        self,
        identifier: str,
        name: str,
        words: dict[str, float],
        description: str | None = None,
    ):
        self.id = identifier
        self.name = name
        self.description = description
        self.words = words if words is not None else {}

    def __repr__(self):
        return f"Topic(id={self.id}, name={self.name}, description={self.description})"


class DocumentTopic(Topic):
    """Class representing a relationship between a document and a topic."""

    def __init__(
        self,
        topic_id: str,
        name: str,
        words: dict[str, float],
        weight: float,
        description: str | None = None,
    ):
        super().__init__(topic_id, name, words, description)
        self.weight = weight if weight is not None else 0.0

    def __repr__(self):
        return f"DocumentTopic(id={self.id}, name={self.name}, description={self.description}, weight={self.weight})"


class User:
    """Class representing a user in the database."""

    def __init__(
        self,
        identifier: str,
        username: str,
        hashed_password: str,
        is_superuser: bool,
        creation_date: str,
    ):
        self.id = identifier
        self.username = username
        self.hashed_password = hashed_password
        self.is_superuser = is_superuser
        self.creation_date = creation_date

    def __repr__(self):
        return f"User(id={self.id}, username={self.username}, is_superuser={self.is_superuser}, creation_date={self.creation_date})"
