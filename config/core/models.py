from django.db import models

from core.enums import VacancyStatus


class BaseModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True


class SearchQuery(BaseModel):
    search_text = models.CharField(max_length=255, db_index=True, verbose_name='Текст запроса')
    in_search = models.BooleanField(default=False, verbose_name='Искать?')

    def __str__(self):
        return self.search_text

    class Meta:
        verbose_name = "Поисковой запрос"
        verbose_name_plural = "Поисковые запросы"


class Area(BaseModel):
    area_id = models.IntegerField(unique=True, db_index=True, verbose_name='ID area')
    parent_id = models.IntegerField(verbose_name='parent_id area')
    name = models.CharField(max_length=255, db_index=True, verbose_name='Название области')
    in_search = models.BooleanField(default=False, verbose_name='Искать?')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Область"
        verbose_name_plural = "Области"


class Vacancy(BaseModel):
    vacancy_id = models.IntegerField(unique=True, db_index=True, verbose_name='ID вакансии')
    watch = models.BooleanField(default=False, verbose_name='Отклик')
    name = models.CharField(max_length=255, db_index=True, verbose_name='Название вакансии')
    area = models.ForeignKey(Area, on_delete=models.PROTECT, verbose_name='Область', related_name="vacancies")
    salary = models.CharField(max_length=255, verbose_name='Зарплата')
    description = models.TextField(verbose_name='Описание вакансии', blank=True)
    employer_name = models.CharField(max_length=255, db_index=True, verbose_name='Название компании')
    employer_url = models.URLField(verbose_name='Ссылка на компанию')
    alternate_url = models.URLField(verbose_name='Ссылка на вакансию')
    status = models.PositiveSmallIntegerField(
        choices=VacancyStatus.choices(), default=VacancyStatus.new.value, verbose_name='Статус'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')
    updated_at = models.DateTimeField(verbose_name='Дата размещения')

    class Meta:
        verbose_name = "Вакансия"
        verbose_name_plural = "Вакансии"


class Profile(BaseModel):
    external_id = models.PositiveIntegerField(unique=True, verbose_name='ID пользователя')
    name = models.TextField(verbose_name='Имя пользователя')

    def __str__(self):
        return f'{self.external_id} {self.name}'

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = 'Профили'


class Message(models.Model):
    profile = models.ForeignKey(Profile, verbose_name='Профиль', on_delete=models.PROTECT, )
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(verbose_name='Время получения', auto_now_add=True)

    def __str__(self):
        return f'Сообщение {self.pk} от {self.profile}'

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
