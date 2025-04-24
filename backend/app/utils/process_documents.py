import os
import pathlib
from datetime import datetime
from time import perf_counter
import pandas as pd

from app.TopicModeling import topic_modeling_v3
from app.utils.theme_naming import generate_name_for_topic
from app.database.documents import (
    get_all_documents,
    get_document_by_filename,
    get_document_topics_by_id,
    process_document,
    link_document_to_topic,
)
from app.database.topics import get_topic_by_name, create_topic, update_topic


def run_process_document():
    documents = get_all_documents()

    start_time = perf_counter()
    try:
        file_path_list = []
        file_name_list = []
        time_list = []
        size_list = []

        for document in documents:
            if os.path.isfile(document.path) and pathlib.Path(document.path).suffix in [
                ".pdf"
            ]:
                file_path_list.append(document.path)
                file_name_list.append(document.filename)
                time_list.append(datetime.timestamp(datetime.fromisoformat(document.upload_date)))
                size_list.append(os.path.getsize(document.path))

        doc_df = pd.DataFrame(
            {
                "file_path": file_path_list,
                "file_name": file_name_list,
                "creation_time": time_list,
                "file_size": size_list,
            }
        )

        topics, doc_topics = topic_modeling_v3.run(doc_df)

        for topic_idx, topic_words_weights in enumerate(topics):
            try:
                topic = get_topic_by_name(f"Topic {topic_idx}")
                if topic is not None:
                    topic.words = {word: weight for word, weight in topic_words_weights}
                    topic.description = generate_name_for_topic(topic_words_weights)

                    update_topic(
                        topic_id=topic.id,
                        name=topic.name,
                        words=topic.words,
                        description=topic.description,
                    )
                else:
                    create_topic(
                        name=f"Topic {topic_idx}",
                        words=dict(topic_words_weights),
                        description=generate_name_for_topic(topic_words_weights),
                    )
            except Exception as e:
                print(f"Error processing topic {topic_idx}: {str(e)}")
                continue

        for doc_topic in doc_topics:
            try:
                document = get_document_by_filename(doc_topic[0])
                if document is not None:
                    document_topics = get_document_topics_by_id(document.id)
                    for topic_idx, weight in enumerate(doc_topic[1]):
                        document_topic_link = [
                            t for t in document_topics if t.name == f"Topic {topic_idx}"
                        ][0] if document_topics else None
                        if document_topic_link is not None:
                            document_topic_link.weight = float(weight)

                            update_topic(
                                topic_id=document_topic_link.topic_id,
                                name=document_topic_link.name,
                                words=document_topic_link.words,
                                description=document_topic_link.description,
                            )
                        else:
                            topic = get_topic_by_name(f"Topic {topic_idx}")
                            if not topic:
                                raise ValueError(f"Topic {topic_idx} not found.")
                            link_document_to_topic(
                                document_id=document.id,
                                topic_id=topic.id,
                                weight=float(weight),
                            )

                    process_document(
                        document_id=document.id,
                    )
            except Exception as e:
                print(f"Error processing document {doc_topic[0]}: {str(e)}")
                continue

    except Exception as e:
        print(f"Process error: {str(e)}")
    finally:
        end_time = perf_counter()
        print(f"Processing completed in: {end_time - start_time:.2f}s")
