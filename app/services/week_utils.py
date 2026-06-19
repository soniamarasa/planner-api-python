from datetime import date, timedelta

WEEKDAY_CODES = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}

EVERGREEN_WHERE = frozenset({"todo", "notes"})


def get_week_start(value: date | None = None) -> date:
    current = value or date.today()
    return current - timedelta(days=current.weekday())


def get_week_end(week_start: date) -> date:
    return week_start + timedelta(days=6)


def is_current_week(week_start: date, today: date | None = None) -> bool:
    today = today or date.today()
    week_end = get_week_end(week_start)
    return week_start <= today <= week_end


def scheduled_date_for_where(week_start: date, where: str | None) -> date | None:
    if not where or where in EVERGREEN_WHERE:
        return None
    offset = WEEKDAY_CODES.get(where)
    if offset is None:
        return None
    return week_start + timedelta(days=offset)


def where_for_scheduled_date(week_start: date, scheduled_date: date) -> str | None:
    delta = (scheduled_date - week_start).days
    for code, offset in WEEKDAY_CODES.items():
        if offset == delta:
            return code
    return None


def is_item_overdue(
    scheduled_date: date | None,
    finished: bool,
    canceled: bool,
    item_type: str | None,
    where: str | None,
    today: date | None = None,
) -> bool:
    today = today or date.today()
    if not scheduled_date or finished or canceled:
        return False
    if where in EVERGREEN_WHERE:
        return False
    if item_type == "note":
        return False
    return scheduled_date < today
