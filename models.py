# models.py
from tortoise import fields
from tortoise.models import Model

class User(Model):
    id = fields.IntField(pk=True)
    telegram_id = fields.CharField(max_length=50, unique=True)
    gamepts = fields.IntField(default=0)
    referral_count = fields.IntField(default=0)
    class Meta:
        table = "user"

class Frens(Model):
    id = fields.IntField(pk=True)
    referrer_id = fields.BigIntField()
    referred = fields.BigIntField()
    class Meta:
        table = "frens"

class Tasks(Model):
    id = fields.IntField(pk=True)
    detail = fields.CharField(max_length=100, unique=False)
    link = fields.CharField(max_length=100, unique=False)
    pts = fields.IntField(max_length=100, unique=False)

    class Meta:
        table = "task"

class CompletedTask(Model):
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='completed_tasks')
    task = fields.ForeignKeyField('models.Tasks', related_name='completed_tasks')
    completed_at = fields.DatetimeField(auto_now_add=True)
