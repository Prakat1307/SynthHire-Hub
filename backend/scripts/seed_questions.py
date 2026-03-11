import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../services/session-orchestrator')))
from sqlalchemy.orm import Session
from app.database import SessionLocal, create_tables
from shared.models.tables import Question, SessionType
import uuid

def seed_questions():
    db: Session = SessionLocal()
    questions = [{'question_text': 'Tell me about a time you had a significant conflict with a teammate. How did you handle it and what was the outcome?', 'question_type': SessionType.BEHAVIORAL, 'difficulty': 4, 'topics': ['conflict-resolution', 'teamwork', 'communication'], 'ideal_response_texts': ['I follow the STAR method. In one project, we disagreed on the architecture. I scheduled a private chat, listened to their concerns, and we reached a middle ground using a trade-off matrix. We successfully launched and preserved our relationship.', 'Conflicts are part of growth. I once had a disagreement over project deadlines. I communicated clearly, showed evidence for my timeline, but also incorporated their suggestions to speed up certain tasks. The outcome was a better schedule for everyone.']}, {'question_text': 'Why do you want to join SynthHire? What interests you specifically about our technology?', 'question_type': SessionType.BEHAVIORAL, 'difficulty': 3, 'topics': ['culture-fit', 'motivation'], 'ideal_response_texts': ["I am passionate about AI-driven assessment. SynthHire's multi-modal approach with facial and audio analysis is cutting-edge and solves real bias problems in hiring.", 'I love building tools that scale. Your service mesh architecture and use of DeBERTa for multi-label classification is exactly the kind of engineering challenge I enjoy.']}, {'question_text': 'Write a function to implement an LRU (Least Recently Used) cache with get and put methods in O(1) time complexity.', 'question_type': SessionType.CODING, 'difficulty': 7, 'topics': ['data-structures', 'hash-map', 'linked-list'], 'starter_code': {'python': 'class LRUCache:\n    def __init__(self, capacity: int):\n        pass\n\n    def get(self, key: int) -> int:\n        pass\n\n    def put(self, key: int, value: int) -> None:\n        pass'}, 'ideal_response_texts': ['You should use a combination of a hash map and a doubly linked list. The hash map provides O(1) access, and the linked list helps maintain the usage order. When a key is accessed or added, move its node to the head. When capacity is exceeded, remove the tail node.', "Implementation requires a dictionary to store key-node pairs and a doubly linked list for order. Python's OrderedDict can also be used as it already implements this behavior."]}, {'question_text': 'Design a URL shortener like bit.ly. How would you handle 10k requests per second and ensure low latency?', 'question_type': SessionType.SYSTEM_DESIGN, 'difficulty': 6, 'topics': ['scalability', 'hashing', 'databases', 'caching'], 'ideal_response_texts': ["I would use a relational database for permanent storage with a unique constraint on the short hash. For low latency, I'd use Redis to cache the most frequently accessed URLs. I'd use Base62 encoding for the hashes to keep them short and URL-safe.", "To handle high load, I'd use a load balancer and multiple app server instances. Hashing can be done using MD5 or SHA256, taking the first 7 characters. For billions of records, I might use NoSQL like Cassandra for easier horizontal scaling."]}]
    try:
        for q_data in questions:
            exists = db.query(Question).filter(Question.question_text == q_data['question_text']).first()
            if not exists:
                q = Question(**q_data)
                db.add(q)
                print(f'Added question: {q.question_text[:50]}...')
        db.commit()
        print('✅ Database seeded successfully!')
    except Exception as e:
        db.rollback()
        print(f'❌ Error seeding database: {e}')
    finally:
        db.close()
if __name__ == '__main__':
    create_tables()
    seed_questions()