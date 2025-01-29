from enum import IntEnum


class VacancyStatus(IntEnum):
    new = 1
    archive = 2
    unavailable = 3
    not_found = 4

    @classmethod
    def choices(cls) -> tuple[tuple[int, str], ...]:
        return (
            (cls.new.value, 'активно'),
            (cls.archive.value, 'в архиве'),
            (cls.unavailable.value, 'недоступна'),
            (cls.not_found.value, 'не найдено')
        )
