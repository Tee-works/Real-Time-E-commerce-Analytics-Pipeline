# Real-time Web Analytics Processing with Kafka

This project demonstrates a real-time web analytics processing pipeline using Kafka and PostgreSQL.

## Components

- Event Generator: Simulates web traffic events
- Page View Processor: Filters and transforms page view events
- User Activity Aggregator: Creates time-window aggregations of user activity
- Database Consumer: Stores processed events in PostgreSQL
