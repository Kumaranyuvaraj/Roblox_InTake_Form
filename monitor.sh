#!/bin/bash
# monitor.sh - Simple monitoring script for manual scaling decisions

echo "📊 Roblox Retainer Performance Monitor"
echo "======================================"
echo "$(date)"
echo ""

# Check Docker containers
echo "🐳 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "Docker not running"
echo ""

# Check system resources
echo "💻 System Resources:"
echo "CPU Usage: $(top -l 1 -s 0 | grep "CPU usage" | awk '{print $3}' 2>/dev/null || echo "N/A")"
echo "Memory Usage: $(free -h 2>/dev/null | grep Mem | awk '{print $3 "/" $2}' || echo "N/A")"
echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5}' 2>/dev/null || echo "N/A")"
echo ""

# Check Celery processing
echo "⚙️  Celery Processing:"
if docker ps | grep -q celery_processing; then
    echo "Processing Queue: $(docker exec $(docker ps -q -f name=celery_processing) celery -A roblex inspect active_queues 2>/dev/null | grep -c "retainer_processing" || echo "0") tasks"
    echo "Submission Queue: $(docker exec $(docker ps -q -f name=celery_submissions) celery -A roblex inspect active_queues 2>/dev/null | grep -c "retainer_submissions" || echo "0") tasks"
else
    echo "Celery workers not running"
fi
echo ""

# Check database
echo "🗄️  Database Status:"
if docker ps | grep -q postgres; then
    echo "Database: Running"
    echo "Connections: $(docker exec $(docker ps -q -f name=db) psql -U ${DB_USER:-roblexuser} -d ${DB_NAME:-roblexdb} -c "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | grep -E "^\s*[0-9]+\s*$" || echo "N/A")"
else
    echo "Database: Not running"
fi
echo ""

# Check recent uploads
echo "📊 Recent Processing:"
echo "Run this in Django shell to check upload status:"
echo "docker exec -it \$(docker ps -q -f name=web) python manage.py shell"
echo ">>> from retainer_app.models import ExcelUpload"
echo ">>> ExcelUpload.objects.filter(status='processing').count()"
echo ""

# Scaling recommendations
echo "🚀 Manual Scaling Recommendations:"
echo "- If CPU > 80%: Upgrade to larger EC2 instance"
echo "- If Memory > 80%: Add more RAM or upgrade instance"
echo "- If processing is slow: Increase Celery worker concurrency"
echo "- If database is slow: Upgrade RDS instance class"
echo ""

echo "💡 Quick Commands:"
echo "- View processing logs: docker-compose logs -f celery_processing"
echo "- View submission logs: docker-compose logs -f celery_submissions"
echo "- Restart workers: docker-compose restart celery_processing celery_submissions"
echo "- Scale up workers: Edit docker-compose.yml concurrency settings"
