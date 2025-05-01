import os
import pathlib
from datetime import datetime
from time import perf_counter
import pandas as pd

from app.config import settings
from app.TopicModeling import topic_modeling_v3
from app.utils.ai_model import generate_name_for_topic
from app.database.documents import (
    get_document_by_filename,
    get_document_topics_by_id,
    set_document_processed,
    link_document_to_topic,
    update_weight_of_document_topic_link,
    delete_document_topic_link,
)
from app.database.topics import get_topic_by_name, create_topic, update_topic

NB_TRESHOLD_LINK = settings.LDA_TRESHOLD_LINK if settings.LDA_TRESHOLD_LINK else 0.01


def run_process_document(documents: list) -> None:
    errors = []

    print("[DOCUMENT PROCESSING] Collecting documents...")
    start_time = perf_counter()
    try:
        file_path_list = []
        file_name_list = []
        document_mined_texts = []
        time_list = []
        size_list = []

        for document in documents:
            if os.path.isfile(document.path) and pathlib.Path(document.path).suffix in settings.ALLOWED_EXTENSIONS:
                file_path_list.append(document.path)
                file_name_list.append(document.filename)
                document_mined_texts.append(document.mined_text)
                time_list.append(
                    datetime.timestamp(datetime.fromisoformat(document.upload_date))
                )
                size_list.append(os.path.getsize(document.path))

        doc_df = pd.DataFrame(
            {
                "file_path": file_path_list,
                "file_name": file_name_list,
                "content": document_mined_texts,
                "creation_time": time_list,
                "file_size": size_list,
            }
        )

        topics, doc_topics = topic_modeling_v3.run(doc_df)

        print(f"[DOCUMENT PROCESSING] Topic modeling completed. Topics: {len(topics)}")
        print("[DOCUMENT PROCESSING] Creating topics...")
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
                errors.append(f"Error processing topic {topic_idx}: {str(e)}")
                continue

        print("[DOCUMENT PROCESSING] Linking documents to topics...")
        for doc_topic in doc_topics:
            try:
                document = get_document_by_filename(doc_topic[0])
                if document is not None:
                    document_topics = get_document_topics_by_id(document.id)
                    for topic_idx, weight in enumerate(doc_topic[1]):
                        existing_topic_matches = (
                            [
                                t for t in document_topics
                                if t.name == f"Topic {topic_idx}"
                            ]
                            if len(document_topics) > 0
                            else []
                        )
                        existing_topic_matches = existing_topic_matches[0] if len(existing_topic_matches) > 0 else None

                        if weight < NB_TRESHOLD_LINK:
                            # Skip topics with low weight
                            if existing_topic_matches is not None:
                                # Remove existing link between document and topic if it exists
                                delete_document_topic_link(
                                    document_id=document.id,
                                    topic_id=existing_topic_matches.id,
                                )
                            continue

                        if existing_topic_matches is not None:
                            # Update existing link if it exists
                            update_weight_of_document_topic_link(
                                document_id=document.id,
                                topic_id=existing_topic_matches.id,
                                weight=float(weight),
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

                    set_document_processed(
                        document_id=document.id,
                    )
            except Exception as e:
                print(f"Error processing document {doc_topic[0]}: {str(e)}")
                errors.append(f"Error processing document {doc_topic[0]}: {str(e)}")
                continue

    except Exception as e:
        print(f"Process error: {str(e)}")
    finally:
        end_time = perf_counter()
        print(
            f"[DOCUMENT PROCESSING] Processing completed in: {end_time - start_time:.2f}s"
        )
        if errors:
            print(f"Document processing errors: {errors}")
            raise RuntimeError(
                f"[DOCUMENT PROCESSING] Document processing failed with errors: {errors}"
            )
