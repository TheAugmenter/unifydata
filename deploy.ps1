# Quick Deploy Script for UnifyData.AI (PowerShell)

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "UnifyData.AI - Deployment Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is initialized
if (-not (Test-Path .git)) {
    Write-Host "❌ Git not initialized. Initializing..." -ForegroundColor Yellow
    git init
    git add .
    git commit -m "Initial commit - Ready for deployment"
    Write-Host "✅ Git initialized" -ForegroundColor Green
}

# Check for uncommitted changes
$status = git status --porcelain
if ($status) {
    Write-Host "📝 Uncommitted changes detected" -ForegroundColor Yellow
    $commit = Read-Host "Do you want to commit all changes? (y/n)"
    if ($commit -eq 'y') {
        git add .
        $message = Read-Host "Enter commit message"
        git commit -m "$message"
        Write-Host "✅ Changes committed" -ForegroundColor Green
    }
}

# Check if remote exists
$remotes = git remote
if (-not ($remotes -contains "origin")) {
    Write-Host "❌ No git remote configured" -ForegroundColor Red
    Write-Host "Please add your GitHub repository:" -ForegroundColor Yellow
    $repo = Read-Host "Enter GitHub repo URL"
    git remote add origin $repo
    Write-Host "✅ Remote added" -ForegroundColor Green
}

# Push to GitHub
Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "✅ Code pushed to GitHub!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend (Vercel):" -ForegroundColor Yellow
Write-Host "1. Go to https://vercel.com/new" -ForegroundColor White
Write-Host "2. Import your GitHub repository" -ForegroundColor White
Write-Host "3. Root Directory: web" -ForegroundColor White
Write-Host "4. Set environment variable:" -ForegroundColor White
Write-Host "   NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app" -ForegroundColor Gray
Write-Host "5. Click Deploy!" -ForegroundColor White
Write-Host ""
Write-Host "Backend (Railway):" -ForegroundColor Yellow
Write-Host "1. Go to https://railway.app/new" -ForegroundColor White
Write-Host "2. Deploy from GitHub repo" -ForegroundColor White
Write-Host "3. Root Directory: backend" -ForegroundColor White
Write-Host "4. Add environment variables (see DEPLOYMENT.md)" -ForegroundColor White
Write-Host "5. Deploy!" -ForegroundColor White
Write-Host ""
Write-Host "📚 See DEPLOYMENT.md for detailed instructions" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
