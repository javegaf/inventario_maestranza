# Generated by Django 5.2.1 on 2025-06-20 00:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0008_alter_proyecto_options_proyecto_creado_por_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracionSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.CharField(choices=[('umbral_stock_critico', 'Umbral de Stock Crítico'), ('umbral_stock_bajo', 'Umbral de Stock Bajo'), ('modo_mantenimiento', 'Modo Mantenimiento'), ('auto_generar_orden_compra', 'Auto-generar Orden de Compra'), ('proveedor_default', 'Proveedor Default'), ('registro_de_auditorias', 'Registro de Auditorías'), ('mostrar_mensaje_bienvenida', 'Mostrar Mensaje de Bienvenida'), ('formato_fecha_preferido', 'Formato de Fecha Preferido')], help_text='Nombre interno del parámetro de configuración.', max_length=100, unique=True)),
                ('valor', models.CharField(help_text='Valor asignado al parámetro (texto o número según contexto).', max_length=255)),
                ('descripcion', models.TextField(blank=True, help_text='Descripción explicativa del propósito de este parámetro.')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuración del Sistema',
                'verbose_name_plural': 'Configuraciones del Sistema',
                'ordering': ['clave'],
            },
        ),
    ]
