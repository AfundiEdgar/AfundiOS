#!/bin/bash
# AfundiOS Docker Helper Script
# Usage: ./docker-help.sh [command]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COLOR_GREEN='\033[0;32m'
COLOR_BLUE='\033[0;34m'
COLOR_YELLOW='\033[1;33m'
COLOR_RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${COLOR_BLUE}ℹ ${1}${NC}"
}

log_success() {
    echo -e "${COLOR_GREEN}✓ ${1}${NC}"
}

log_warn() {
    echo -e "${COLOR_YELLOW}⚠ ${1}${NC}"
}

log_error() {
    echo -e "${COLOR_RED}✗ ${1}${NC}"
}

# Check if .env exists
check_env() {
    if [ ! -f .env ]; then
        log_warn ".env file not found"
        log_info "Creating .env from .env.example..."
        cp .env.example .env
        log_success ".env created. Please edit it with your configuration."
    fi
}

# Build images
build() {
    log_info "Building Docker images..."
    docker-compose build "$@"
    log_success "Build complete"
}

# Start services
start() {
    check_env
    log_info "Starting services..."
    docker-compose up -d
    log_success "Services started"
    log_info "Backend: http://localhost:8000"
    log_info "Frontend: http://localhost:8501"
    log_info "API Docs: http://localhost:8000/docs"
}

# Stop services
stop() {
    log_info "Stopping services..."
    docker-compose down
    log_success "Services stopped"
}

# View logs
logs() {
    docker-compose logs -f "$@"
}

# Development mode (with hot-reload)
dev() {
    log_warn "Development mode: enabling hot-reload"
    log_info "Uncomment development sections in docker-compose.yml for hot-reload"
    check_env
    docker-compose up
}

# Clean up containers and volumes
clean() {
    log_warn "Cleaning up containers, networks, and volumes..."
    docker-compose down -v
    log_success "Cleanup complete"
}

# Health check
health() {
    log_info "Checking service health..."
    
    if docker-compose ps --services --filter "status=running" | grep -q backend; then
        if curl -sf http://localhost:8000/ > /dev/null; then
            log_success "Backend is healthy"
        else
            log_error "Backend health check failed"
        fi
    else
        log_error "Backend is not running"
    fi

    if docker-compose ps --services --filter "status=running" | grep -q frontend; then
        if curl -sf http://localhost:8501/_stcore/health > /dev/null; then
            log_success "Frontend is healthy"
        else
            log_error "Frontend health check failed"
        fi
    else
        log_error "Frontend is not running"
    fi
}

# Show status
status() {
    log_info "Docker Compose Status:"
    docker-compose ps
}

# Restart services
restart() {
    log_info "Restarting services..."
    docker-compose restart "$@"
    log_success "Services restarted"
}

# Pull latest images (if using registry)
pull() {
    log_info "Pulling latest images from registry..."
    docker-compose pull "$@"
    log_success "Pull complete"
}

# Push images (if using registry)
push() {
    log_warn "Pushing images to registry (ensure you're logged in)"
    docker-compose push "$@"
    log_success "Push complete"
}

# Shell into container
shell() {
    local service="${1:-backend}"
    log_info "Opening shell in $service container..."
    docker-compose exec "$service" /bin/bash
}

# Run tests
test() {
    log_info "Running tests..."
    docker-compose exec backend python -m pytest tests/ -v
}

# Show help
show_help() {
    cat << EOF
${COLOR_BLUE}AfundiOS Docker Helper${NC}

Usage: ./docker-help.sh [command] [options]

Commands:
    ${COLOR_GREEN}start${NC}       Start all services (production mode)
    ${COLOR_GREEN}dev${NC}         Start services with hot-reload (development mode)
    ${COLOR_GREEN}stop${NC}        Stop all services
    ${COLOR_GREEN}build${NC}       Build Docker images
    ${COLOR_GREEN}restart${NC}     Restart services
    ${COLOR_GREEN}status${NC}      Show service status
    ${COLOR_GREEN}logs${NC}        View logs (e.g., ./docker-help.sh logs backend)
    ${COLOR_GREEN}health${NC}      Check service health
    ${COLOR_GREEN}shell${NC}       Open shell in container (e.g., ./docker-help.sh shell backend)
    ${COLOR_GREEN}clean${NC}       Remove containers and volumes (WARNING: deletes data)
    ${COLOR_GREEN}pull${NC}        Pull images from registry
    ${COLOR_GREEN}push${NC}        Push images to registry
    ${COLOR_GREEN}test${NC}        Run test suite
    ${COLOR_GREEN}help${NC}        Show this help message

Examples:
    ./docker-help.sh start              # Start all services
    ./docker-help.sh logs backend       # View backend logs
    ./docker-help.sh logs -f            # View all logs (follow)
    ./docker-help.sh shell frontend     # Open shell in frontend
    ./docker-help.sh restart backend    # Restart only backend

For more information, see DOCKER_DEPLOYMENT.md

EOF
}

# Main
case "${1:-help}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart "${@:2}"
        ;;
    build)
        build "${@:2}"
        ;;
    dev)
        dev
        ;;
    logs)
        logs "${@:2}"
        ;;
    health)
        health
        ;;
    status)
        status
        ;;
    clean)
        log_warn "About to delete all containers, networks, and volumes."
        read -p "Are you sure? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            clean
        else
            log_info "Cancelled"
        fi
        ;;
    shell)
        shell "${@:2}"
        ;;
    pull)
        pull "${@:2}"
        ;;
    push)
        push "${@:2}"
        ;;
    test)
        test "${@:2}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
