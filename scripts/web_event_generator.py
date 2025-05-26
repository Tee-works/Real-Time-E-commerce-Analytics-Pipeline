import json
import time
import random
import uuid
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.app_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS
from confluent_kafka import Producer
import ipaddress

# Configure Kafka producer
producer_config = {
    'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS[0]
}
producer = Producer(producer_config)

# Sample data for simulation
pages = [
    "/home", "/products", "/category/electronics", "/category/clothing",
    "/product/12345", "/cart", "/checkout", "/about", "/contact", "/login"
]

actions = ["pageview", "click", "scroll", "form_submit", "video_play"]

devices = ["mobile", "desktop", "tablet"]
browsers = ["chrome", "firefox", "safari", "edge"]
os_names = ["windows", "macos", "android", "ios", "linux"]

# Helper functions
def generate_ip():
    # Generate random IP addresses (avoid reserved ranges)
    return str(ipaddress.IPv4Address(random.randint(0x01000000, 0xDF000000)))

def generate_session_id():
    return str(uuid.uuid4())

def generate_user_id():
    # 20% chance of anonymous user (no user_id)
    if random.random() < 0.2:
        return None
    return f"user_{random.randint(1, 1000)}"

def generate_timestamp():
    return datetime.now().isoformat()

# Create a pool of users and sessions for more realistic simulation
user_sessions = {}
for i in range(1, 101):  # Create 100 users
    user_id = f"user_{i}"
    user_sessions[user_id] = generate_session_id()

# Delivery callback
def delivery_callback(err, msg):
    if err:
        print(f'× Message delivery failed: {err}')
    else:
        print(f"✓ Sent event to {msg.topic()} [{msg.partition()}]")

# Generate and send events
def generate_event():
    # Sometimes create new session for existing user
    if random.random() < 0.05:  # 5% chance to regenerate session for a user
        user_id = random.choice(list(user_sessions.keys()))
        user_sessions[user_id] = generate_session_id()
    
    # Select a user (or anonymous)
    user_id = generate_user_id()
    
    # If user is not anonymous, use their existing session
    session_id = user_sessions.get(user_id, generate_session_id()) if user_id else generate_session_id()
    
    event = {
        "event_id": str(uuid.uuid4()),
        "timestamp": generate_timestamp(),
        "user_id": user_id,
        "session_id": session_id,
        "ip_address": generate_ip(),
        "page": random.choice(pages),
        "action": random.choice(actions),
        "device": {
            "type": random.choice(devices),
            "browser": random.choice(browsers),
            "os": random.choice(os_names)
        },
        "referrer": random.choice(pages + [None, None, None]),  # 3/5 chance of no referrer
        "load_time": round(random.uniform(0.5, 5.0), 2) if random.random() < 0.8 else None
    }
    
    # Add action-specific data
    if event["action"] == "click":
        event["click_target"] = random.choice(["button", "link", "image", "nav"])
    elif event["action"] == "scroll":
        event["scroll_depth"] = random.randint(10, 100)
    
    return event

def send_event(event):
    try:
        # Convert event to JSON
        event_json = json.dumps(event)
        # Send to Kafka
        producer.produce(KAFKA_TOPICS['raw_events'], event_json.encode('utf-8'), callback=delivery_callback)
        producer.poll(0)  # Trigger delivery callbacks
        print(f"Producing: {event['action']} on {event['page']}")
        return True
    except Exception as e:
        print(f"× Failed to send event: {e}")
        return False

# Main loop
try:
    print("Starting web event generator. Press Ctrl+C to exit.")
    event_count = 0
    
    while True:
        # Generate between 1-5 events
        for _ in range(random.randint(1, 5)):
            event = generate_event()
            if send_event(event):
                event_count += 1
            
            # Generate related events (when a pageview might lead to clicks)
            if event["action"] == "pageview" and random.random() < 0.7:
                # 70% chance that a pageview leads to other actions
                for _ in range(random.randint(1, 3)):
                    follow_up = generate_event()
                    follow_up["user_id"] = event["user_id"]
                    follow_up["session_id"] = event["session_id"]
                    follow_up["page"] = event["page"]
                    follow_up["action"] = random.choice(["click", "scroll"])
                    follow_up["ip_address"] = event["ip_address"]
                    follow_up["device"] = event["device"]
                    
                    if send_event(follow_up):
                        event_count += 1
        
        # Status update every 50 events
        if event_count % 50 == 0 and event_count > 0:
            print(f"Generated {event_count} events so far")
            
        # Random delay between 0.1 and 1 second
        time.sleep(random.uniform(0.1, 1.0))
        
        # Flush producer periodically
        producer.poll(0)
        
except KeyboardInterrupt:
    print("\nStopping event generator")
finally:
    # Flush any remaining messages
    producer.flush(30)
    print(f"Generated {event_count} events in total")
