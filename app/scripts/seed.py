from datetime import date

from sqlalchemy import select

from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.focus_settings import FocusSettings
from app.models.item import Item
from app.models.user import User


def run() -> None:
    db = SessionLocal()
    try:
        email = "demo@planner.dev"
        existing_user = db.scalar(select(User).where(User.email == email))
        if existing_user:
            print("Seed already applied")
            return

        user = User(
            name="Demo User",
            email=email,
            password=get_password_hash("12345678"),
            birthdate=date(1995, 5, 17),
            gender="female",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        focus_settings = FocusSettings(user_id=user.id)
        db.add(focus_settings)

        items = [
            Item(
                user_id=user.id,
                description="Estudar FastAPI",
                type="task",
                where="mon",
                obs="Revisar rotas e dependencias",
                started=False,
                finished=False,
                important=True,
                canceled=False,
                estimated_pomodoros=2.0,
            ),
            Item(
                user_id=user.id,
                description="Planejar dashboard de analytics",
                type="note",
                where="todo",
                obs="Separar metricas de produtividade",
                started=False,
                finished=False,
                important=False,
                canceled=False,
            ),
        ]

        db.add_all(items)
        db.commit()
        print("Seed applied successfully")
    finally:
        db.close()


if __name__ == "__main__":
    run()