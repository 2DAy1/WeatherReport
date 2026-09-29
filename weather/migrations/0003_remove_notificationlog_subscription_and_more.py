from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("weather_app", "0002_subscription_next_run_at"),
        ("subscriptions", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(model_name="notificationlog", name="subscription"),
                migrations.RemoveField(model_name="notificationlog", name="weather_data"),
                migrations.AlterUniqueTogether(name="subscription", unique_together=None),
                migrations.RemoveField(model_name="subscription", name="city"),
                migrations.RemoveField(model_name="subscription", name="user"),
                migrations.DeleteModel(name="NotificationLog"),
                migrations.DeleteModel(name="Subscription"),
                migrations.AlterModelTable(name="city", table="weather_app_city"),
                migrations.AlterModelTable(name="weatherdata", table="weather_app_weatherdata"),
            ],
        ),
    ]
