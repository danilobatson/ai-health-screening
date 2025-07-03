#!/bin/bash
# Manual Vercel deployment script

echo "🚀 Starting manual Vercel deployment"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Confirm user is logged in
echo "🔑 Checking Vercel login status..."
vercel whoami || vercel login

# Deploy to production
echo "🚀 Deploying to production..."
vercel --prod

echo "✅ Deployment command complete"
echo "📋 Check your Vercel dashboard for deployment status"
echo "🔗 https://vercel.com/dashboard"
