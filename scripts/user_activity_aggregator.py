import json
import time
from datetime import datetime
import sys
import os
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.app_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS
from confluent_kafka import Consumer, Producer

# Set up consumer
consumer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS[0],
    'group.id': 'user-activity-aggregator-group',
    'auto.offset.reset': 'earliest'
}
consumer = Consumer(consumer_config)
consumer.subscribe([KAFKA_TOPICS['raw_events']])

# Set up producer
producer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS[0]
}
producer = Producer(producer_config)

# Track user activity in memory
user_activity = defaultdict(lambda: {
    'pageviews': 0,
    'clicks': 0,
    'scrolls': 0,
    'form_submits': 0,
    'video_plays': 0,
    'pages': set(),
    'last_seen': None
})

# Window settings (1-minute windows)
window_size_sec = 60
last_window_time = time.time()

# Delivery callback
def delivery_callback(err, msg):
    if err:
        print(f'Message delivery failed: {err}')
    else:
        print(f"Activity data sent to {msg.topic()} [{msg.partition()}]")

print("Starting User Activity Aggregator")
try:
    while True:
        # Poll for messages
        msg = consumer.poll(1.0)
        
        current_time = time.time()
        
        # Process message if available
        if msg is not None and not msg.error():
            try:
                event = json.loads(msg.value().decode('utf-8'))
                
                # Skip anonymous users
                if not event['user_id']:
                    continue
                
                user_id = event['user_id']
                action = event['action']
                
                # Update user activity
                user_activity[user_id][action + 's'] += 1
                user_activity[user_id]['pages'].add(event['page'])
                user_activity[user_id]['last_seen'] = event['timestamp']
            except Exception as e:
                print(f"Error processing message: {e}")
        
        # Check if window time has elapsed
        if current_time - last_window_time >= window_size_sec:
            # Time to aggregate and send data
            window_end_time = datetime.now().isoformat()
            
            print(f"Aggregating user activity at {window_end_time}")
            
            # Process each user's activity
            for user_id, activity in user_activity.items():
                # Convert set of pages to list for JSON serialization
                activity_copy = activity.copy()
                activity_copy['pages'] = list(activity['pages'])
                
                # Add metadata
                aggregate = {
                    'user_id': user_id,
                    'window_end_time': window_end_time,
                    'activity': activity_copy
                }
                
                # Send aggregated data
                producer.produce(
                    KAFKA_TOPICS['user_activity'],
                    json.dumps(aggregate).encode('utf-8'),
                    callback=delivery_callback
                )
                producer.poll(0)  # Trigger delivery callbacks
            
            # Reset for next window
            user_activity.clear()
            last_window_time = current_time
            
            # Ensure data is sent
            producer.flush()
            
except KeyboardInterrupt:
    print("Shutting down User Activity Aggregator")
finally:
    consumer.close()
