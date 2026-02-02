#!/bin/bash

# TorWAR Docker Management Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_banner() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║         TorWAR - Docker Management                    ║"
    echo "║         AWS Well-Architected Review Tool              ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}[-] Docker not found. Please install Docker first.${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}[-] Docker Compose not found. Please install Docker Compose first.${NC}"
        exit 1
    fi
}

build() {
    print_banner
    echo -e "${GREEN}[+] Building TorWAR Docker image...${NC}"
    docker-compose build
    echo -e "${GREEN}[+] Build complete!${NC}"
}

start() {
    print_banner
    echo -e "${GREEN}[+] Starting TorWAR...${NC}"
    docker-compose up -d
    echo ""
    echo -e "${GREEN}[+] TorWAR is running!${NC}"
    echo -e "${YELLOW}Access at: http://localhost:5000${NC}"
    echo ""
}

stop() {
    echo -e "${YELLOW}[*] Stopping TorWAR...${NC}"
    docker-compose down
    echo -e "${GREEN}[+] TorWAR stopped${NC}"
}

restart() {
    stop
    sleep 2
    start
}

logs() {
    docker-compose logs -f
}

status() {
    docker-compose ps
}

shell() {
    echo -e "${GREEN}[+] Opening shell in TorWAR container...${NC}"
    docker-compose exec torwar bash
}

clean() {
    echo -e "${RED}[!] This will remove all containers, images, and volumes.${NC}"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose down -v
        docker rmi torwar-torwar 2>/dev/null || true
        echo -e "${GREEN}[+] Cleanup complete${NC}"
    else
        echo -e "${YELLOW}[*] Cleanup cancelled${NC}"
    fi
}

help() {
    print_banner
    echo "Usage: $0 {command}"
    echo ""
    echo "Commands:"
    echo "  build      Build Docker image"
    echo "  start      Start TorWAR container"
    echo "  stop       Stop TorWAR container"
    echo "  restart    Restart TorWAR container"
    echo "  logs       View container logs"
    echo "  status     Show container status"
    echo "  shell      Open shell in container"
    echo "  clean      Remove all containers and images"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build"
    echo "  $0 start"
    echo "  $0 logs"
    echo ""
}

# Main
check_docker

case "$1" in
    build)
        build
        ;;
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    shell)
        shell
        ;;
    clean)
        clean
        ;;
    help|--help|-h|"")
        help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        help
        exit 1
        ;;
esac
