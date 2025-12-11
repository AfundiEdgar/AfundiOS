#!/bin/bash

# Redis Setup Script for AfundiOS
# This script helps you set up Redis for caching

set -e

echo "🚀 Setting up Redis for AfundiOS caching..."

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Redis based on OS
install_redis() {
    echo "📦 Installing Redis..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt-get; then
            # Ubuntu/Debian
            sudo apt-get update
            sudo apt-get install -y redis-server
        elif command_exists yum; then
            # CentOS/RHEL
            sudo yum install -y redis
        elif command_exists dnf; then
            # Fedora
            sudo dnf install -y redis
        else
            echo "❌ Unsupported Linux distribution. Please install Redis manually."
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install redis
        else
            echo "❌ Homebrew not found. Please install Homebrew first or install Redis manually."
            exit 1
        fi
    else
        echo "❌ Unsupported operating system. Please install Redis manually."
        exit 1
    fi
}

# Function to start Redis service
start_redis() {
    echo "🔄 Starting Redis service..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - try systemctl first, then service
        if command_exists systemctl; then
            sudo systemctl start redis-server || sudo systemctl start redis
            sudo systemctl enable redis-server || sudo systemctl enable redis
        elif command_exists service; then
            sudo service redis-server start || sudo service redis start
        else
            # Manual start
            redis-server --daemonize yes
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS with brew
        brew services start redis
    fi
}

# Function to test Redis connection
test_redis() {
    echo "🔍 Testing Redis connection..."
    
    if command_exists redis-cli; then
        if redis-cli ping > /dev/null 2>&1; then
            echo "✅ Redis is running and responding to pings"
            return 0
        else
            echo "❌ Redis is not responding"
            return 1
        fi
    else
        echo "❌ redis-cli not found"
        return 1
    fi
}

# Function to setup Redis with Docker
setup_redis_docker() {
    echo "🐳 Setting up Redis with Docker..."
    
    if ! command_exists docker; then
        echo "❌ Docker not found. Please install Docker first."
        exit 1
    fi
    
    # Start Redis container
    echo "Starting Redis container..."
    docker-compose -f docker-compose.redis.yml up -d
    
    # Wait for Redis to be ready
    echo "Waiting for Redis to be ready..."
    sleep 5
    
    # Test connection
    if docker exec afundios-redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis container is running and ready"
        echo "📊 Redis Commander UI available at: http://localhost:8081"
    else
        echo "❌ Redis container failed to start properly"
        exit 1
    fi
}

# Function to update environment file
update_env_file() {
    echo "⚙️ Updating environment configuration..."
    
    ENV_FILE=".env"
    
    if [ ! -f "$ENV_FILE" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
    fi
    
    # Update Redis settings in .env file
    if grep -q "REDIS_ENABLED=" "$ENV_FILE"; then
        sed -i 's/REDIS_ENABLED=.*/REDIS_ENABLED=true/' "$ENV_FILE"
    else
        echo "REDIS_ENABLED=true" >> "$ENV_FILE"
    fi
    
    echo "✅ Updated $ENV_FILE with Redis configuration"
}

# Main execution
main() {
    echo "Choose Redis setup method:"
    echo "1) Install Redis natively (recommended for development)"
    echo "2) Use Docker (recommended for production/containers)"
    echo "3) Skip installation (Redis already installed)"
    read -p "Enter your choice (1-3): " choice
    
    case $choice in
        1)
            if command_exists redis-server && test_redis; then
                echo "✅ Redis is already installed and running"
            else
                install_redis
                start_redis
            fi
            ;;
        2)
            setup_redis_docker
            ;;
        3)
            echo "Skipping Redis installation..."
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
    
    # Test the final setup
    if test_redis || docker exec afundios-redis redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis setup completed successfully!"
        
        # Update environment file
        update_env_file
        
        echo ""
        echo "🎉 Redis caching is now configured for AfundiOS!"
        echo ""
        echo "Next steps:"
        echo "  1. Install Python dependencies: pip install -r requirements.txt"
        echo "  2. Start your application: python backend/main.py"
        echo "  3. Check cache status: curl http://localhost:8000/cache/health"
        echo ""
        echo "Redis configuration:"
        echo "  - Host: localhost"
        echo "  - Port: 6379"
        echo "  - Database: 0"
        if docker ps --format '{{.Names}}' | grep -q afundios-redis; then
            echo "  - Redis Commander UI: http://localhost:8081"
        fi
        echo ""
        
    else
        echo "❌ Redis setup failed. Please check the installation and try again."
        exit 1
    fi
}

# Run main function
main "$@"