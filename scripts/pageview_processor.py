import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.app_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS
from confluent_kafka import Consumer, Producer

# Set up the consumer
consumer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS[0],
    'group.id': 'pageview-processor-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)
consumer.subscribe([KAFKA_TOPICS['raw_events']])

# Set up the producer
producer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS[0]
}
producer = Producer(producer_config)

# Delivery callback
def delivery_callback(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f"Pageview sent to {msg.topic()} [{msg.partition()}]")

print("Starting Page View Processor")
try:
    while True:
        # Poll for messages
        msg = consumer.poll(1.0)
        
        if msg is None:
            continue
        
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue
        
        # Parse the message
        try:
            event = json.loads(msg.value().decode('utf-8'))
            
            # Filter for pageview events
            if event['action'] == 'pageview':
                # Extract relevant data
                pageview = {
                    'event_id': event['event_id'],
                    'timestamp': event['timestamp'],
                    'user_id': event['user_id'],
                    'session_id': event['session_id'],
                    'page': event['page'],
                    'device_type': event['device']['type'],
                    'load_time': event['load_time']
                }
                
                print(f"Processing pageview for page: {pageview['page']}")
                
                # Send to pageviews topic
                producer.produce(
                    KAFKA_TOPICS['page_views'],
                    json.dumps(pageview).encode('utf-8'),
                    callback=delivery_callback
                )
                producer.poll(0)  # Trigger delivery callbacks
        except Exception as e:
            print(f"Error processing message: {e}")
            
except KeyboardInterrupt:
    print("Shutting down Page View Processor")
finally:
    consumer.close()
