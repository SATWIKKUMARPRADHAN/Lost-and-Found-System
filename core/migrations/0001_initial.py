# Generated for Campus Lost and Found Management System

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(help_text='Short, clear title describing the item', max_length=200)),
                ('description', models.TextField(help_text='Provide public visual details without giving away the secret verification answer')),
                ('category', models.CharField(choices=[('ELECTRONICS', 'Electronics & Gadgets'), ('BOOKS', 'Books, Notebooks & Stationary'), ('ID_CARDS', 'Cards, IDs & Wallets'), ('CLOTHING', 'Clothing, Bags & Accessories'), ('KEYS', 'Keys & Keychain Sets'), ('JEWELRY', 'Watches & Jewelry'), ('BOTTLES', 'Bottles, Umbrellas & Personal Gear'), ('OTHER', 'Other Belongings')], default='OTHER', max_length=30)),
                ('location', models.CharField(help_text='Specific campus building, room, or landmark', max_length=150)),
                ('incident_date', models.DateField(help_text='Date when item was lost or found')),
                ('item_type', models.CharField(choices=[('LOST', 'Lost Item (I lost something)'), ('FOUND', 'Found Item (I found something)')], default='LOST', max_length=10)),
                ('image', models.ImageField(blank=True, help_text='Optional photograph of the item', null=True, upload_to='items/%Y/%m/')),
                ('status', models.CharField(choices=[('OPEN', 'Open'), ('CLAIMED', 'Claimed (Pending Transfer)'), ('RETURNED', 'Returned to Owner')], default='OPEN', max_length=15)),
                ('verification_question', models.CharField(blank=True, help_text="For FOUND items: A question only the genuine owner can answer (e.g., 'What sticker is on the laptop back lid?')", max_length=255)),
                ('verification_answer_hash', models.CharField(blank=True, help_text='Secure PBKDF2/Argon2 cryptographic hash of the expected answer', max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reported_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reported_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('PENDING', 'Pending Admin Review'), ('APPROVED', 'Approved (Ready for Handover)'), ('REJECTED', 'Rejected')], default='PENDING', max_length=15)),
                ('verification_passed', models.BooleanField(default=False, help_text='Indicates whether claimant solved the secret verification question')),
                ('claim_note', models.TextField(blank=True, help_text='Additional proof or explanation provided by claimant during verification')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('claimant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='submitted_claims', to=settings.AUTH_USER_MODEL)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='claims', to='core.item')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
