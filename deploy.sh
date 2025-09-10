#!/bin/bash

# SecureAI Vercel Deployment Script
# This script helps deploy both frontend and backend to Vercel

set -e

echo "🚀 SecureAI Vercel Deployment Script"
echo "======================================"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed"
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please login to Vercel:"
    vercel login
fi

echo ""
echo "Choose deployment option:"
echo "1. Deploy/Redeploy Backend only"
echo "2. Deploy/Redeploy Frontend only"
echo "3. Deploy/Redeploy Both (Full Stack)"
echo "4. Just redeploy existing projects (no new deployments)"
read -p "Enter your choice (1-4): " choice

# Function to redeploy existing project
redeploy_existing() {
    local project_name=$1
    echo "🔄 Redeploying existing project: $project_name"
    
    # Try to redeploy using project name
    if vercel --prod --yes; then
        echo "✅ Successfully redeployed $project_name"
    else
        echo "⚠️  Direct redeploy failed, trying fresh deployment..."
        vercel --prod
    fi
}

case $choice in
    1|3)
        echo ""
        echo "🔧 Deploying Backend..."
        echo "Root directory: $(pwd)"
        
        # Check if .env file exists
        if [ ! -f .env ]; then
            echo "⚠️  No .env file found. Backend will use environment variables from Vercel dashboard"
            echo "📝 Make sure to set OPENAI_API_KEY in Vercel dashboard"
        fi
        
        # Deploy backend (this will redeploy if project exists)
        if vercel --prod --yes; then
            echo "✅ Backend deployed/redeployed successfully!"
        else
            echo "⚠️  Deployment failed, trying interactive mode..."
            vercel --prod
        fi
        
        echo ""
        ;;
esac

case $choice in
    2|3)
        echo ""
        echo "🎨 Deploying Frontend..."
        cd frontend
        
        # Check if node_modules exists
        if [ ! -d "node_modules" ]; then
            echo "📦 Installing frontend dependencies..."
            npm install
        fi
        
        # Deploy frontend (this will redeploy if project exists)
        if vercel --prod --yes; then
            echo "✅ Frontend deployed/redeployed successfully!"
        else
            echo "⚠️  Deployment failed, trying interactive mode..."
            vercel --prod
        fi
        
        cd ..
        echo ""
        ;;
esac

case $choice in
    4)
        echo ""
        echo "🔄 Redeploying existing projects..."
        echo ""
        
        # Backend redeploy
        echo "🔧 Redeploying Backend..."
        if vercel --prod --yes; then
            echo "✅ Backend redeployed successfully!"
        else
            echo "❌ Backend redeploy failed"
        fi
        
        echo ""
        
        # Frontend redeploy
        echo "🎨 Redeploying Frontend..."
        cd frontend
        if vercel --prod --yes; then
            echo "✅ Frontend redeployed successfully!"
        else
            echo "❌ Frontend redeploy failed"
        fi
        cd ..
        
        echo ""
        ;;
esac

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📋 Your Deployed URLs:"
echo "Backend: Check https://vercel.com/dashboard for your backend URL"
echo "Frontend: Check https://vercel.com/dashboard for your frontend URL"
echo ""
echo "🔧 Environment Variables Needed:"
echo "Backend:"
echo "  - OPENAI_API_KEY=your_openai_key (optional for lightweight version)"
echo ""
echo "Frontend:"
echo "  - VITE_API_URL=https://your-backend-url.vercel.app"
echo ""
echo "📊 Quick Test:"
echo "1. Visit your backend URL to see: {\"message\": \"SecureAI Lightweight API\"}"
echo "2. Visit your frontend URL to see the full application"
echo ""
echo "🔗 Useful Commands:"
echo "   vercel ls              # List your deployments"
echo "   vercel logs            # View deployment logs"
echo "   vercel env             # Manage environment variables"
echo ""
echo "Happy deploying! 🚀"