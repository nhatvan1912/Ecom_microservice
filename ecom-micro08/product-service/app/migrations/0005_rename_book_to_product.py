from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0004_search_behavior_models'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Book',
            new_name='Product',
        ),
        migrations.RenameField(
            model_name='product',
            old_name='author',
            new_name='brand',
        ),
        migrations.AlterField(
            model_name='product',
            name='brand',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='app.category'),
        ),
        migrations.RenameField(
            model_name='review',
            old_name='book',
            new_name='product',
        ),
        migrations.RenameField(
            model_name='searchbehaviorevent',
            old_name='book_id',
            new_name='product_id',
        ),
        migrations.RenameField(
            model_name='searchbehaviorevent',
            old_name='book_ids',
            new_name='product_ids',
        ),
        migrations.RenameField(
            model_name='searchuserprofile',
            old_name='book_weights',
            new_name='product_weights',
        ),
    ]
