from django.db import models

# Create your models here.

class Links(models.Model):
    name = models.CharField(default='',max_length=20000)
    course = models.CharField(default='', max_length=20000)
    link = models.CharField(default='', max_length=20000000000000)

    class Meta:
        verbose_name_plural = 'Links'
    def __str__(self):
        return  f'{self.name} Link'

class Files(models.Model):
    name = models.CharField(default='',max_length=100000)
    document = models.FileField(upload_to='files/', default='')
    course = models.CharField(default='', max_length=20000)
    description = models.CharField(default='', max_length=2000000)

    class Meta:
        verbose_name_plural = 'Files'

    def __str__(self):
        return f'{sel.name} for  course {self.course }'

