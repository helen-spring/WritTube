from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        help_text='Текст Вашей записи',
        verbose_name='Текст'
    )
    pub_date = models.DateTimeField("date_published", auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        help_text='Выберите жанр',
        verbose_name='Группа'
    )
    image = models.ImageField(
        upload_to='posts/',
        blank=True,
        null=True,
        verbose_name='Изображение'
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        return self.text


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    text = models.TextField(
        max_length=1000,
        help_text='Текст комментария',
        verbose_name='Комментарий'
    )
    created = models.DateTimeField("created_date", auto_now_add=True)

    class Meta:
        ordering = ['-created']


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="follower"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following"
    )
