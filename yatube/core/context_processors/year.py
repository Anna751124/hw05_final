from datetime import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    dt = datetime.utcnow().year
    return {
        'year': dt
    }
