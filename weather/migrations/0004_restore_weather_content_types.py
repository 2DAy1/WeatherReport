from django.db import migrations


def restore_weather_content_types(apps, schema_editor):
    content_type = apps.get_model("contenttypes", "ContentType")
    database = schema_editor.connection.alias
    for model in ("city", "weatherdata"):
        previous = content_type.objects.using(database).filter(app_label="weather", model=model).first()
        current = content_type.objects.using(database).filter(app_label="weather_app", model=model).exists()
        if previous and not current:
            previous.app_label = "weather_app"
            previous.save(update_fields=["app_label"])


class Migration(migrations.Migration):
    dependencies = [
        ("weather_app", "0003_remove_notificationlog_subscription_and_more"),
        ("subscriptions", "0002_transfer_content_types"),
    ]

    operations = [migrations.RunPython(restore_weather_content_types, migrations.RunPython.noop)]
