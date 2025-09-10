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
echo "1. Deploy Backend only"
echo "2. Deploy Frontend only"
echo "3. Deploy Both (Full Stack)"
read -p "Enter your choice (1-3): " choice

case $choice in
    1|3)
        echo ""
        echo "🔧 Deploying Backend..."
        echo "Root directory: $(pwd)"
        
        # Check if .env file exists
        if [ ! -f .env ]; then
            echo "⚠️  No .env file found. Please create one with your OPENAI_API_KEY"
            echo "📝 Example: cp .env.example .env"
            read -p "Continue anyway? (y/N): " continue_backend
            if [[ $continue_backend != "y" && $continue_backend != "Y" ]]; then
                exit 1
            fi
        fi
        
        # Deploy backend
        vercel --prod
        
        echo "✅ Backend deployed successfully!"
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
        
        # Deploy frontend
        vercel --prod
        
        echo "✅ Frontend deployed successfully!"
        cd ..
        echo ""
        ;;
esac

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to https://vercel.com/dashboard"
echo "2. Find your deployed projects"
echo "3. Set up environment variables:"
echo "   - Backend: OPENAI_API_KEY, CREWAI_MODEL"
echo "   - Frontend: VITE_API_URL (pointing to your backend URL)"
echo "4. Test your deployment!"
echo ""
echo "🔗 Useful Commands:"
echo "   vercel domains         # Manage custom domains"
echo "   vercel env             # Manage environment variables"
echo "   vercel logs            # View deployment logs"
echo ""
echo "Happy deploying! 🚀"