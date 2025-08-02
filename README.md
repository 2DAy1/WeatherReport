# Django Weather Reminder

A Django-based weather notification service that sends periodic weather updates to users via email and webhooks using Celery background tasks.

## Features

- **User Authentication**: JWT-based authentication system
- **City Management**: Search and manage cities for weather monitoring
- **Subscription System**: Users can subscribe to weather notifications for multiple cities
- **Multiple Notification Types**: Email and webhook notifications
- **Cost Optimization**: 
  - Caches weather data to avoid duplicate API calls
  - Groups notifications by city to minimize API requests
  - Sends consolidated emails for multiple cities
- **Background Processing**: Celery tasks for async weather fetching and notification sending
- **Parallel Processing**: Weather API calls and email sending are parallelized
- **Periodic Tasks**: Automated weather notifications every hour
- **Docker Support**: Complete containerized deployment

## Architecture

### Models
- **User**: Django's built-in User model
- **City**: Stores city information with coordinates
- **Subscription**: User subscriptions to weather notifications
- **WeatherData**: Cached weather data to optimize API calls
- **NotificationLog**: Tracks notification delivery status

### Background Tasks
- **Weather Data Fetching**: Parallel fetching from OpenWeatherMap API
- **Email Notifications**: HTML and text email templates
- **Webhook Notifications**: JSON payloads to external services
- **Bulk Processing**: Optimized for multiple users and cities
- **Data Cleanup**: Automatic cleanup of old weather data

## Setup Instructions

### Prerequisites
- Python 3.11+
- Redis (for Celery broker)
- PostgreSQL (optional, SQLite for development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CursorWeatherReminder
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   OPENWEATHER_API_KEY=your-openweather-api-key
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-email-password
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Populate sample data**
   ```bash
   python manage.py populate_data
   ```

8. **Start Redis** (required for Celery)
   ```bash
   # On Windows, download Redis from https://redis.io/download
   # On macOS: brew install redis && brew services start redis
   # On Ubuntu: sudo apt-get install redis-server
   ```

9. **Start Celery worker**
   ```bash
   celery -A weather_reminder worker -l info
   ```

10. **Start Celery beat** (for periodic tasks)
    ```bash
    celery -A weather_reminder beat -l info
    ```

11. **Run the development server**
    ```bash
    python manage.py runserver
    ```

### Docker Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations in container**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Populate sample data**
   ```bash
   docker-compose exec web python manage.py populate_data
   ```

## API Documentation

### Authentication

#### Register User
```http
POST /api/register/
Content-Type: application/json

{
    "username": "john_doe",
    "email": "john@example.com",
    "password": "password123",
    "password_confirm": "password123",
    "first_name": "John",
    "last_name": "Doe"
}
```

#### Get JWT Token
```http
POST /api/token/
Content-Type: application/json

{
    "username": "john_doe",
    "password": "password123"
}
```

#### Refresh Token
```http
POST /api/token/refresh/
Content-Type: application/json

{
    "refresh": "your-refresh-token"
}
```

### Cities

#### List Cities
```http
GET /api/cities/
Authorization: Bearer <your-access-token>
```

#### Search Cities
```http
GET /api/cities/search/?q=London
Authorization: Bearer <your-access-token>
```

### Subscriptions

#### List User Subscriptions
```http
GET /api/subscriptions/
Authorization: Bearer <your-access-token>
```

#### Create Subscription
```http
POST /api/subscriptions/
Authorization: Bearer <your-access-token>
Content-Type: application/json

{
    "city": 1,
    "notification_period": 1,
    "notification_type": "email"
}
```

#### Update Subscription
```http
PUT /api/subscriptions/1/
Authorization: Bearer <your-access-token>
Content-Type: application/json

{
    "city": 1,
    "notification_period": 2,
    "notification_type": "webhook",
    "webhook_url": "https://webhook.site/your-unique-url"
}
```

#### Toggle Subscription Active Status
```http
POST /api/subscriptions/1/toggle_active/
Authorization: Bearer <your-access-token>
```

#### Get Active Subscriptions
```http
GET /api/subscriptions/active/
Authorization: Bearer <your-access-token>
```

### Weather Data

#### Get Weather by City
```http
GET /api/weather/by_city/?city_id=1
Authorization: Bearer <your-access-token>
```

### Notification Logs

#### List Notification Logs
```http
GET /api/notifications/
Authorization: Bearer <your-access-token>
```

#### Get Recent Notifications
```http
GET /api/notifications/recent/
Authorization: Bearer <your-access-token>
```

## Cost Optimization Features

### Weather API Optimization
- **Caching**: Weather data is cached for 30 minutes to avoid duplicate API calls
- **Parallel Processing**: Multiple city weather requests are processed in parallel
- **Grouping**: Multiple users requesting the same city get the same cached data

### Email Optimization
- **Consolidated Emails**: Users with multiple city subscriptions receive one email with all weather data
- **Parallel Sending**: Email notifications are sent in parallel using Celery

### Webhook Optimization
- **Timeout Management**: Webhook requests have configurable timeouts
- **Error Handling**: Failed webhook attempts are logged and can be retried

## Background Tasks

### Periodic Tasks
- **Hourly Notifications**: Sends weather notifications every hour
- **Daily Cleanup**: Removes weather data older than 7 days

### Manual Task Execution
```python
# Fetch weather for a specific city
from weather_app.tasks import fetch_weather_data_for_city
fetch_weather_data_for_city.delay(city_id)

# Send notifications for a user
from weather_app.tasks import send_notifications_for_user
send_notifications_for_user.delay(user_id)

# Send bulk notifications
from weather_app.tasks import send_bulk_notifications
send_bulk_notifications.delay()
```

## Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## Deployment

### Production Settings
Update `settings.py` for production:
- Set `DEBUG = False`
- Configure proper database (PostgreSQL recommended)
- Set up proper email backend
- Configure static files serving
- Set secure `SECRET_KEY`

### Environment Variables
```env
SECRET_KEY=your-production-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com
DATABASE_URL=postgresql://user:password@host:port/db
OPENWEATHER_API_KEY=your-api-key
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
CELERY_BROKER_URL=redis://redis:6379/0
```

## Monitoring

### Celery Monitoring
- Use Flower for Celery monitoring: `pip install flower`
- Run: `celery -A weather_reminder flower`

### Logging
- Application logs are configured in `settings.py`
- Celery task logs include success/failure information
- Notification logs track delivery status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License. 