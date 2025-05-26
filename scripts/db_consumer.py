import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.app_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS, DB_CONFIG
from confluent_kafka import Consumer
import psycopg2

# Database connection
conn = psycopg2.connect(
    dbname=DB_CONFIG['dbname'],
    user=DB_CONFIG['user'],
    host=DB_CONFIG['host'],
    password=DB_CONFIG['password']
)
cursor = conn.cursor()

# Set up consumer
consumer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS[0],
    'group.id': 'postgres-consumer-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)
consumer.subscribe([KAFKA_TOPICS['page_views']])

print("Starting Database Consumer for Page Views")
try:
    while True:
        # Poll for messages
        msg = consumer.poll(1.0)
        
        if msg is None:
            continue
        
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        
        # Process valid message
        try:
            pageview = json.loads(msg.value().decode('utf-8'))
            
            # Convert None to NULL for SQL
            user_id = pageview['user_id'] if pageview['user_id'] else None
            load_time = pageview['load_time'] if pageview['load_time'] else None
            
            cursor.execute(
                "INSERT INTO pageviews (event_id, timestamp, user_id, session_id, page, device_type, load_time) " +
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    pageview['event_id'],
                    pageview['timestamp'],
                    user_id,
                    pageview['session_id'],
                    pageview['page'],
                    pageview['device_type'],
                    load_time
                )
            )
            conn.commit()
            print(f"Stored pageview: {pageview['page']}")
        except Exception as e:
            print(f"Error storing pageview: {e}")
            conn.rollback()
            
except KeyboardInterrupt:
    print("Shutting down Database Consumer")
finally:
    cursor.close()
    conn.close()
    consumer.close()
