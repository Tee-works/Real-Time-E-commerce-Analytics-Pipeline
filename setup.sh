#!/bin/bash

# Real-Time E-commerce Analytics Pipeline Setup Script
set -e  # Exit on any error

echo "🚀 Setting up Real-Time E-commerce Analytics Pipeline..."
echo "====================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check dependencies
check_dependencies() {
    echo "Checking dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗${NC} Python 3 is required but not installed"
        exit 1
    fi
    print_status "Python 3 found"
    
    if ! command -v java &> /dev/null; then
        echo -e "${RED}✗${NC} Java is required but not installed"
        exit 1
    fi
    print_status "Java found"
    
    if ! command -v psql &> /dev/null; then
        print_warning "PostgreSQL client not found. Please ensure PostgreSQL is installed"
    else
        print_status "PostgreSQL client found"
    fi
}

# Setup Python environment
setup_python_env() {
    echo "Setting up Python environment..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_status "Python dependencies installed"
    else
        print_warning "requirements.txt not found"
    fi
}

# Setup Kafka
setup_kafka() {
    echo "Setting up Apache Kafka..."
    
    if [ ! -f "kafka_2.13-3.9.0.tgz" ] && [ ! -d "kafka_2.13-3.9.0" ]; then
        echo "Downloading Kafka..."
        wget https://downloads.apache.org/kafka/3.9.0/kafka_2.13-3.9.0.tgz
        print_status "Kafka downloaded"
    fi
    
    if [ ! -d "kafka_2.13-3.9.0" ]; then
        tar -xzf kafka_2.13-3.9.0.tgz
        print_status "Kafka extracted"
    else
        print_status "Kafka already extracted"
    fi
    
    if [ ! -L "kafka" ]; then
        ln -sf kafka_2.13-3.9.0 kafka
        print_status "Kafka symlink created"
    fi
}

# Main execution
main() {
    check_dependencies
    setup_python_env
    setup_kafka
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start Kafka: ./kafka/bin/zookeeper-server-start.sh kafka/config/zookeeper.properties"
    echo "2. Start Kafka server: ./kafka/bin/kafka-server-start.sh kafka/config/server.properties"
    echo "3. Run the analytics pipeline components"
}

main "$@"
