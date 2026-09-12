import asyncio
from typing import List, Tuple
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.database import AsyncSessionLocal
from app.models.category import Category

# Exactly 12 categories as specified in Task 1.3
SEED_CATEGORIES = [
    {"name": "Rent", "description": "House / flat rent and housing maintenance", "is_income": False},
    {"name": "Groceries", "description": "Supermarkets, daily food and provisions", "is_income": False},
    {"name": "Utilities", "description": "Electricity, water, gas, internet, mobile bills", "is_income": False},
    {"name": "Transport", "description": "Fuel, cabs (Uber/Ola), metro, transit", "is_income": False},
    {"name": "Dining", "description": "Restaurants, food delivery (Swiggy/Zomato), cafes", "is_income": False},
    {"name": "Shopping", "description": "Clothing, electronics, online commerce", "is_income": False},
    {"name": "Entertainment", "description": "Movies, events, games, leisure", "is_income": False},
    {"name": "Subscriptions", "description": "Streaming, digital memberships, recurring software", "is_income": False},
    {"name": "Medical", "description": "Healthcare, doctor fees, pharmacy, medical tests", "is_income": False},
    {"name": "Salary Credit", "description": "Monthly payroll and salary credits from employer", "is_income": True},
    {"name": "Miscellaneous", "description": "General and miscellaneous expenditures", "is_income": False},
    {"name": "Self-Transfer", "description": "Transfers between user's own accounts or wallet loads", "is_income": False},
]


def seed_categories_sync(session: Session) -> Tuple[int, List[Category]]:
    """
    Seeds the 12 canonical categories synchronously into the database idempotently.
    Returns (created_count, all_categories).
    """
    created_count = 0
    all_categories: List[Category] = []

    for cat_data in SEED_CATEGORIES:
        statement = select(Category).where(Category.name == cat_data["name"])
        result = session.exec(statement)
        existing = result.first()

        if existing is None:
            new_cat = Category(
                name=cat_data["name"],
                description=cat_data["description"],
                is_income=cat_data["is_income"],
                is_system=True,
            )
            session.add(new_cat)
            created_count += 1
            all_categories.append(new_cat)
        else:
            all_categories.append(existing)

    if created_count > 0:
        session.commit()
        for cat in all_categories:
            session.refresh(cat)

    return created_count, all_categories


async def seed_categories(session: AsyncSession) -> Tuple[int, List[Category]]:
    """
    Seeds the 12 canonical categories asynchronously into the database idempotently.
    Returns (created_count, all_categories).
    """
    created_count = 0
    all_categories: List[Category] = []

    for cat_data in SEED_CATEGORIES:
        statement = select(Category).where(Category.name == cat_data["name"])
        result = await session.execute(statement)
        existing = result.scalars().first()

        if existing is None:
            new_cat = Category(
                name=cat_data["name"],
                description=cat_data["description"],
                is_income=cat_data["is_income"],
                is_system=True,
            )
            session.add(new_cat)
            created_count += 1
            all_categories.append(new_cat)
        else:
            all_categories.append(existing)

    if created_count > 0:
        await session.commit()
        for cat in all_categories:
            await session.refresh(cat)

    return created_count, all_categories


async def main() -> None:
    print(f"Connecting to database to seed {len(SEED_CATEGORIES)} categories...")
    async with AsyncSessionLocal() as session:
        created, all_cats = await seed_categories(session)
        print(f"Seeding complete! Newly created: {created}, Total existing categories: {len(all_cats)}")
        for idx, cat in enumerate(all_cats, 1):
            print(f"  {idx:2d}. {cat.name:<15} (ID: {cat.id}, Income: {cat.is_income})")


if __name__ == "__main__":
    asyncio.run(main())
