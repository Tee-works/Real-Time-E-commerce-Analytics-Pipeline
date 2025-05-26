# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = ['localhost:9092']
KAFKA_TOPICS = {
    'raw_events': 'raw-events',
    'page_views': 'page-views',
    'user_activity': 'user-activity',
    'alerts': 'alerts'
}

# Database configuration
DB_CONFIG = {
    'dbname': 'webanalytics',
    'user': 'postgres',
    'password': 'taiwo',
    'host': 'localhost',
    'port': '5432'
}

# Application settings
LOG_LEVEL = 'INFO'