#!/bin/bash

echo "🚀 Deploying DjangoWeatherReminder to Google App Engine..."

# Install Google Cloud SDK (if not installed)
# curl https://sdk.cloud.google.com | bash
# exec -l $SHELL

# Set project ID
PROJECT_ID="your-project-id-here"

# Initialize gcloud
gcloud init --project=$PROJECT_ID

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

# Deploy to App Engine
echo "🚀 Deploying to Google App Engine..."
gcloud app deploy app.yaml --project=$PROJECT_ID

echo "✅ Deployment completed!"
echo "🌐 Your app is available at: https://weather-reminder-dot-$PROJECT_ID.appspot.com" 