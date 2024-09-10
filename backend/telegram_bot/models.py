from django.db import models


class TgChat(models.Model):
    id = models.CharField(primary_key=True, max_length=100)


class TgMessage(models.Model):
    tg_chat = models.ForeignKey(TgChat, on_delete=models.CASCADE)
    name = models.CharField(default='', max_length=50)
    username = models.CharField(default='', max_length=50)
    message = models.TextField()
    user_id = models.CharField(max_length=50)
    date_time = models.DateTimeField()
