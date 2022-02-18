from django.db import models


class BaseModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True


class Area(BaseModel):
    area_id = models.IntegerField(unique=True, db_index=True, verbose_name='ID area')
    parent_id = models.IntegerField(verbose_name='parent_id area')
    name = models.CharField(max_length=255, db_index=True, verbose_name='Название области')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Область"
        verbose_name_plural = "Области"


class Vacancy(BaseModel):
    vacancy_id = models.IntegerField(unique=True, db_index=True, verbose_name='ID вакансии')
    area = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name='Область', related_name="vacancies")
    title = models.CharField(max_length=255, db_index=True, verbose_name='Название вакансии')
    company = models.CharField(max_length=255, db_index=True, verbose_name='Название компании')
    url_company = models.URLField(verbose_name='Ссылка на компанию')
    url_vacancy = models.URLField(verbose_name='Ссылка на вакансию')
    status_choices = (
        ('new', 'активно'),
        ('archive', 'в архиве'),
        ('unavailable', 'недоступна'),
    )
    status = models.CharField(max_length=150, choices=status_choices, default='new', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(verbose_name='Дата размещения')
    salary = models.CharField(max_length=255, verbose_name='Зарплата')

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"
