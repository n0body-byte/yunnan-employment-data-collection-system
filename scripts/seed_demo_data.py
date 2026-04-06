from __future__ import annotations

from sqlalchemy import select

from app.database import SessionLocal, engine
from app.enums import FilingStatus, UserRole
from app.models import Base, Enterprise, User
from app.security import hash_password


def seed_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = [
            {
                "username": "province_admin",
                "password": "Admin12345",
                "role": UserRole.PROVINCE,
                "region": "Yunnan",
            },
            {
                "username": "kunming_city",
                "password": "City12345",
                "role": UserRole.CITY,
                "region": "Kunming",
            },
            {
                "username": "demo_enterprise",
                "password": "Enterprise12345",
                "role": UserRole.ENTERPRISE,
                "region": "Kunming",
            },
        ]

        for item in users:
            existing = db.scalar(select(User).where(User.username == item["username"]))
            if existing is None:
                db.add(
                    User(
                        username=item["username"],
                        password_hash=hash_password(item["password"]),
                        role=item["role"],
                        region=item["region"],
                    )
                )
        db.commit()

        enterprise_user = db.scalar(select(User).where(User.username == "demo_enterprise"))
        if enterprise_user is not None:
            existing_enterprise = db.scalar(select(Enterprise).where(Enterprise.owner_user_id == enterprise_user.id))
            if existing_enterprise is None:
                db.add(
                    Enterprise(
                        owner_user_id=enterprise_user.id,
                        organization_code="YN1234567",
                        name="Demo Enterprise",
                        nature="Private Enterprise",
                        industry="Manufacturing/Equipment",
                        main_business="Industrial manufacturing",
                        contact_person="Demo Contact",
                        phone="13800138000",
                        region="Kunming",
                        address="Kunming High-tech Zone",
                        postal_code="650000",
                        fax=None,
                        email="demo@example.com",
                        filing_status=FilingStatus.APPROVED,
                    )
                )
                db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
    print("Demo data seeded successfully.")
