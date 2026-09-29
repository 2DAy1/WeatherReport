# Django Weather Reminder

A Django-based weather notification service that sends periodic weather updates to users via email and webhooks using Celery background tasks.

The scheduler checks due subscriptions every minute. Each subscription has its own
`next_run_at` and a 1, 3, 6, or 12 hour interval. Local Docker email delivery uses the
console backend. See [notification scheduling](docs/notification-scheduling.md)
for the task flow, tests, and delivery limitations.

## Features

- **User Authentication**: JWT-based authentication system
- **Cities**: List and search cities available for weather monitoring
- **Subscription System**: Users can subscribe to weather notifications for multiple cities
- **Multiple Notification Types**: Email and webhook notifications
- **Cost Optimization**: 
  - Caches weather data to avoid duplicate API calls
  - Groups notifications by city to minimize API requests
- **Background Processing**: Celery tasks for async weather fetching and notification sending
- **Parallel Processing**: Independent Celery tasks process weather requests and deliveries
- **Periodic Tasks**: Checks due subscriptions every minute and respects their notification intervals
- **Docker Support**: Local development with Docker Compose

## Architecture

### Django apps
- **`accounts`**: user registration; authentication uses Django's built-in User and Simple JWT
- **`weather`**: City, WeatherData, OpenWeatherMap request, weather and cleanup tasks
- **`subscriptions`**: Subscription, NotificationLog, scheduling, email and webhook tasks
- **`weather_reminder`**: Django settings, root routes, and Celery configuration

The API paths remain unchanged. Historical migrations live in `weather/migrations/` under the retained Django label `weather_app`; the models use their existing database tables. See [architecture](docs/architecture.md) for the class diagram, module roles and migration design.

### Background Tasks
- **Weather Data Fetching**: Parallel fetching from OpenWeatherMap API
- **Email Notifications**: HTML and text email templates
- **Webhook Notifications**: JSON payloads to external services
- **Bulk Processing**: Optimized for multiple users and cities
- **Data Cleanup**: Automatic cleanup of old weather data

## Setup Instructions

### Prerequisites
- Python 3.12
- Redis (for Celery broker)
- PostgreSQL (optional, SQLite for development)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd djangoweatherreminder
   ```

2. **Create virtual environment**
   ```bash
   py -3.12 -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```bash
   python -m pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   OPENWEATHER_API_KEY=your-openweather-api-key
   EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

5. **Run migrations**
   ```bash
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

1. **Add `OPENWEATHER_API_KEY` to `.env`, then build and run with Docker Compose**
   ```bash
   docker compose up --build
   ```

   The `web` container applies migrations on startup.

2. **Populate sample data**
   ```bash
   docker compose exec web python manage.py populate_data
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
    "notification_period": 3,
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
- **Console Email**: Local notifications appear in the Celery worker logs
- **Independent Delivery**: Each email is queued as a Celery task

### Webhook Optimization
- **Timeout Management**: Webhook requests have configurable timeouts
- **Error Handling**: Failed webhook attempts are logged

## Background Tasks

### Periodic Tasks
- **Scheduled Notifications**: Checks subscriptions every minute; queues notifications when their 1, 3, 6, or 12 hour interval is due
- **Daily Cleanup**: Removes weather data older than 7 days

### Manual Task Execution
```python
# Fetch weather for a specific city
from weather.tasks import fetch_weather_data_for_city
fetch_weather_data_for_city.delay(city_id)

# Send bulk notifications
from subscriptions.tasks import send_bulk_notifications
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
