#!/usr/bin/env python3
"""
Alert Processor for Real-Time E-commerce Analytics Pipeline
Monitors key business metrics and system health, triggering alerts when thresholds are exceeded.
"""

import json
import time
import logging
from datetime import datetime, timedelta
from confluent_kafka import Consumer, Producer
import psycopg2
import sys
import os

# Add the parent directory to the path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.app_config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPICS, DB_CONFIG, LOG_LEVEL

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AlertProcessor:
    def __init__(self):
        # Use your existing config format
        self.kafka_servers = KAFKA_BOOTSTRAP_SERVERS[0] if isinstance(KAFKA_BOOTSTRAP_SERVERS, list) else KAFKA_BOOTSTRAP_SERVERS
        self.topics = KAFKA_TOPICS
        self.db_config = DB_CONFIG
        
        self.consumer = Consumer({
            'bootstrap.servers': self.kafka_servers,
            'group.id': 'alert-processors',
            'auto.offset.reset': 'latest'
        })
        
        self.producer = Producer({
            'bootstrap.servers': self.kafka_servers
        })
        
        # Subscribe to topics we want to monitor
        self.consumer.subscribe([self.topics['page_views'], self.topics['user_activity']])
        
        # Alert thresholds
        self.alert_rules = {
            'high_error_rate': {'threshold': 0.05, 'window_minutes': 5},
            'low_conversion_rate': {'threshold': 0.02, 'window_minutes': 15},
            'high_cart_abandonment': {'threshold': 0.80, 'window_minutes': 10},
            'slow_page_load': {'threshold': 3000, 'window_minutes': 5},  # 3 seconds
            'low_traffic': {'threshold': 100, 'window_minutes': 10}      # events per 10 min
        }
        
        self.last_alert_times = {}  # Prevent alert spam
        
    def get_db_connection(self):
        """Get database connection using your existing config"""
        return psycopg2.connect(**self.db_config)
    
    def check_conversion_rate(self):
        """Check if conversion rate is below threshold"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get conversion data from last 15 minutes
            query = """
            SELECT 
                COUNT(CASE WHEN page = '/checkout' THEN 1 END) as checkouts,
                COUNT(CASE WHEN page = '/purchase-complete' THEN 1 END) as purchases
            FROM pageviews 
            WHERE timestamp > NOW() - INTERVAL '15 minutes'
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result[0] > 0:  # Only check if we have checkouts
                conversion_rate = result[1] / result[0]
                threshold = self.alert_rules['low_conversion_rate']['threshold']
                
                if conversion_rate < threshold:
                    self.send_alert(
                        'low_conversion_rate',
                        f'Conversion rate dropped to {conversion_rate:.2%} (threshold: {threshold:.2%})',
                        'warning',
                        {'checkouts': result[0], 'purchases': result[1], 'rate': conversion_rate}
                    )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking conversion rate: {e}")
    
    def check_page_performance(self):
        """Check for slow page load times"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get average load time from last 5 minutes
            query = """
            SELECT AVG(load_time), COUNT(*) 
            FROM pageviews 
            WHERE timestamp > NOW() - INTERVAL '5 minutes'
              AND load_time IS NOT NULL
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result and result[1] > 10:  # Only alert if we have sufficient data
                avg_load_time = result[0]
                threshold = self.alert_rules['slow_page_load']['threshold']
                
                if avg_load_time > threshold:
                    self.send_alert(
                        'slow_page_load',
                        f'Average page load time: {avg_load_time:.0f}ms (threshold: {threshold}ms)',
                        'warning',
                        {'avg_load_time': avg_load_time, 'sample_size': result[1]}
                    )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking page performance: {e}")
    
    def check_traffic_volume(self):
        """Check for unusually low traffic"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Get event count from last 10 minutes
            query = """
            SELECT COUNT(*) 
            FROM pageviews 
            WHERE timestamp > NOW() - INTERVAL '10 minutes'
            """
            
            cursor.execute(query)
            result = cursor.fetchone()
            
            if result:
                event_count = result[0]
                threshold = self.alert_rules['low_traffic']['threshold']
                
                if event_count < threshold:
                    self.send_alert(
                        'low_traffic',
                        f'Low traffic detected: {event_count} events in 10 minutes (threshold: {threshold})',
                        'info',
                        {'event_count': event_count, 'time_window': '10 minutes'}
                    )
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking traffic volume: {e}")
    
    def send_alert(self, alert_type, message, severity, metadata=None):
        """Send alert to alerts topic and log"""
        # Prevent alert spam - only send same alert type once per hour
        current_time = datetime.now()
        last_alert = self.last_alert_times.get(alert_type)
        
        if last_alert and (current_time - last_alert) < timedelta(hours=1):
            return
        
        alert_data = {
            'alert_id': f"{alert_type}_{int(current_time.timestamp())}",
            'alert_type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': current_time.isoformat(),
            'metadata': metadata or {}
        }
        
        try:
            # Send to Kafka alerts topic
            self.producer.produce(
                self.topics['alerts'],
                key=alert_type,
                value=json.dumps(alert_data)
            )
            self.producer.flush()
            
            # Log the alert
            logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")
            
            # Store in database if table exists
            self.store_alert_in_db(alert_data)
            
            # Update last alert time
            self.last_alert_times[alert_type] = current_time
            
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
    
    def store_alert_in_db(self, alert_data):
        """Store alert in database for historical tracking"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Check if alerts table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'alerts'
                );
            """)
            
            if cursor.fetchone()[0]:  # Table exists
                query = """
                INSERT INTO alerts (alert_type, severity, message, timestamp, metadata) 
                VALUES (%s, %s, %s, %s, %s)
                """
                
                cursor.execute(query, (
                    alert_data['alert_type'],
                    alert_data['severity'],
                    alert_data['message'],
                    alert_data['timestamp'],
                    json.dumps(alert_data['metadata'])
                ))
                
                conn.commit()
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store alert in database: {e}")
    
    def run_health_checks(self):
        """Run all health checks"""
        logger.info("Running e-commerce health checks...")
        
        self.check_conversion_rate()
        self.check_page_performance()
        self.check_traffic_volume()
        
        logger.info("Health checks completed")
    
    def run(self):
        """Main processing loop"""
        logger.info("Starting Alert Processor for E-commerce Analytics")
        logger.info(f"Kafka servers: {self.kafka_servers}")
        logger.info(f"Database: {self.db_config['host']}:{self.db_config['port']}")
        
        last_health_check = datetime.now()
        
        try:
            while True:
                # Run health checks every 2 minutes
                if datetime.now() - last_health_check > timedelta(minutes=2):
                    self.run_health_checks()
                    last_health_check = datetime.now()
                
                # Check for real-time events
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                    
                if msg.error():
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
                
                time.sleep(1)  # Prevent excessive CPU usage
                
        except KeyboardInterrupt:
            logger.info("Alert processor stopped")
        except Exception as e:
            logger.error(f"Alert processor error: {e}")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    processor = AlertProcessor()
    processor.run()
