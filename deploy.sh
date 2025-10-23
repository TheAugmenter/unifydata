#!/bin/bash
# Quick Deploy Script for UnifyData.AI

echo "=========================================="
echo "UnifyData.AI - Deployment Script"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git not initialized. Initializing..."
    git init
    git add .
    git commit -m "Initial commit - Ready for deployment"
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Uncommitted changes detected"
    read -p "Do you want to commit all changes? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add .
        read -p "Enter commit message: " commit_msg
        git commit -m "$commit_msg"
    fi
fi

# Check if remote exists
if ! git remote | grep -q origin; then
    echo "❌ No git remote configured"
    echo "Please add your GitHub repository:"
    read -p "Enter GitHub repo URL: " repo_url
    git remote add origin "$repo_url"
fi

# Push to GitHub
echo ""
echo "🚀 Pushing to GitHub..."
git push origin main

echo ""
echo "=========================================="
echo "✅ Code pushed to GitHub!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Go to https://vercel.com/new"
echo "2. Import your GitHub repository"
echo "3. Set NEXT_PUBLIC_API_URL environment variable"
echo "4. Deploy!"
echo ""
echo "For backend:"
echo "1. Go to https://railway.app/new"
echo "2. Deploy from GitHub repo"
echo "3. Configure environment variables"
echo ""
echo "See DEPLOYMENT.md for detailed instructions"
echo "=========================================="
