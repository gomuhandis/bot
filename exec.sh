#!/bin/bash

set -e

echo "🐍 Python Docker setup boshlanmoqda..."

# Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY .env .

CMD ["python", "bot.py"]
EOF

# docker-compose.yml
cat > docker-compose.yml <<'EOF'
services:
  bot:
    build: .
    container_name: python-bot
    restart: unless-stopped
    env_file:
      - .env
EOF

# .dockerignore
cat > .dockerignore <<'EOF'
.git
.gitignore
__pycache__
*.pyc
*.pyo
*.pyd
.venv
venv
EOF

echo "✅ Dockerfile yaratildi"
echo "✅ docker-compose.yml yaratildi"
echo "✅ .dockerignore yaratildi"

# Git
if [ ! -d ".git" ]; then
    git init
fi

git add Dockerfile docker-compose.yml .dockerignore bot.py requirements.txt .env

git commit -m "Add Docker setup for Python bot" || true

echo ""
echo "Git remote:"
git remote -v || true

echo ""
read -p "Git remote URL ni kiriting: " REMOTE

if [ -n "$REMOTE" ]; then
    git remote remove origin 2>/dev/null || true
    git remote add origin "$REMOTE"
fi

BRANCH=$(git branch --show-current)

if [ -z "$BRANCH" ]; then
    git branch -M main
    BRANCH="main"
fi

echo ""
echo "🚀 Git push qilinmoqda..."

git push -u origin "$BRANCH"

echo ""
echo "✅ Tayyor!"