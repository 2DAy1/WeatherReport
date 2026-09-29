from django.db import migrations


def transfer_content_types(apps, schema_editor):
    content_type = apps.get_model("contenttypes", "ContentType")
    mapping = {
        "subscription": "subscriptions",
        "notificationlog": "subscriptions",
    }
    for model, new_app in mapping.items():
        old = content_type.objects.using(schema_editor.connection.alias).filter(
            app_label="weather_app", model=model,
        ).first()
        if old and not content_type.objects.using(schema_editor.connection.alias).filter(
            app_label=new_app, model=model,
        ).exists():
            old.app_label = new_app
            old.save(update_fields=["app_label"])


class Migration(migrations.Migration):
    dependencies = [
        ("subscriptions", "0001_initial"),
        ("weather_app", "0003_remove_notificationlog_subscription_and_more"),
    ]

    operations = [
        migrations.RunPython(transfer_content_types, migrations.RunPython.noop),
    ]
