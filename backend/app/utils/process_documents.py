from datetime import datetime
from time import perf_counter
import os
import pathlib
import pandas as pd
from sqlmodel import Session, select

from app.TopicModeling import topic_modeling_v3
from app.models import Document, DocumentTopicLink, Topic


def run_process_document(documents, session: Session):
    start_time = perf_counter()
    try:
        file_path_list = []
        file_name_list = []
        time_list = []
        size_list = []

        for document in documents:
            if os.path.isfile(document.path) and pathlib.Path(document.path).suffix in ['.pdf']:
                file_path_list.append(document.path)
                file_name_list.append(document.filename)
                time_list.append(datetime.timestamp(document.upload_date))
                size_list.append(os.path.getsize(document.path))

        doc_df = pd.DataFrame({
                'file_path': file_path_list,
                'file_name': file_name_list, 
                'creation_time': time_list,
                'file_size': size_list
            })

        topics, doc_topics = topic_modeling_v3.run(doc_df)

        for topic_idx, topic_words_weights in enumerate(topics):
            try:
                topic = session.exec(select(Topic).where(Topic.name == f"Topic {topic_idx}")).first()
                if topic:
                    topic.words = {word: weight for word, weight in topic_words_weights}
                else:
                    topic = Topic(
                        name=f"Topic {topic_idx}",
                        words={word: weight for word, weight in topic_words_weights}
                    )
                    session.add(topic)
                session.commit()
                session.refresh(topic)
            except Exception as e:
                print(f"Error processing topic {topic_idx}: {str(e)}")
                session.rollback()
                continue
        
        for doc_topic in doc_topics:
            try:
                document = session.exec(select(Document).where(Document.filename == doc_topic[0])).first()
                if document:
                    for topic_idx, weight in enumerate(doc_topic[1]):
                        topic = session.exec(select(Topic).where(Topic.name == f"Topic {topic_idx}")).first()
                        document_topic_link = session.exec(
                            select(DocumentTopicLink)
                            .where(DocumentTopicLink.document_id == document.id)
                            .where(DocumentTopicLink.topic_id == topic.id)
                        ).first()
                        if document_topic_link:
                            document_topic_link.weight = float(weight)
                        else:
                            document_topic_link = DocumentTopicLink(
                                document_id=document.id,
                                topic_id=topic.id,
                                weight=float(weight)
                            )
                            session.add(document_topic_link)
                        session.commit()

                document.processed = True
                session.add(document)
                session.commit()
            except Exception as e:
                print(f"Error processing document {doc_topic[0]}: {str(e)}")
                session.rollback()
                continue

    except Exception as e:
        print(f"Process error: {str(e)}")
        session.rollback()
    finally:
        end_time = perf_counter()
        session.close()
        print(f"Processing completed in: {end_time - start_time:.2f}s")