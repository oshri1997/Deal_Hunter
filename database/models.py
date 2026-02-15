from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user ID
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    premium_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    regions: Mapped[list["UserRegion"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    wishlist: Mapped[list["UserWishlist"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserRegion(Base):
    __tablename__ = "user_regions"

    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), primary_key=True)
    region_code: Mapped[str] = mapped_column(String(5), primary_key=True)

    user: Mapped["User"] = relationship(back_populates="regions")


class UserWishlist(Base):
    __tablename__ = "user_wishlist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    game_id: Mapped[str] = mapped_column(String(255), ForeignKey("games.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="wishlist")
    game: Mapped["Game"] = relationship()

    __table_args__ = (UniqueConstraint("user_id", "game_id"),)


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # PSN game ID
    title: Mapped[str] = mapped_column(String(500))
    cover_url: Mapped[str | None] = mapped_column(Text)
    genre: Mapped[str | None] = mapped_column(String(100))
    platform: Mapped[str | None] = mapped_column(String(10))  # PS5, PS4

    prices: Mapped[list["Price"]] = relationship(back_populates="game", cascade="all, delete-orphan")
    active_deals: Mapped[list["ActiveDeal"]] = relationship(back_populates="game", cascade="all, delete-orphan")


class Price(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(255), ForeignKey("games.id"))
    region_code: Mapped[str] = mapped_column(String(5))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    original_price: Mapped[float] = mapped_column(Numeric(10, 2))
    discount_percent: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(5))
    sale_end_date: Mapped[datetime | None] = mapped_column(DateTime)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    game: Mapped["Game"] = relationship(back_populates="prices")


class ActiveDeal(Base):
    __tablename__ = "active_deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    game_id: Mapped[str] = mapped_column(String(255), ForeignKey("games.id"))
    region_code: Mapped[str] = mapped_column(String(5))
    price: Mapped[float] = mapped_column(Numeric(10, 2))
    original_price: Mapped[float] = mapped_column(Numeric(10, 2))
    discount_percent: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(5))
    sale_end_date: Mapped[datetime | None] = mapped_column(DateTime)
    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    price_tag: Mapped[str | None] = mapped_column(String(50))  # "New lowest!", "Lowest", etc.
    page_number: Mapped[int] = mapped_column(Integer, default=1)  # Which page
    position_on_page: Mapped[int] = mapped_column(Integer, default=0)  # Position 0-35

    game: Mapped["Game"] = relationship(back_populates="active_deals")

    __table_args__ = (
        UniqueConstraint("game_id", "region_code"),
        Index("idx_active_deals_region_first_seen", "region_code", "first_seen"),
        Index("idx_active_deals_region_page_pos", "region_code", "page_number", "position_on_page"),
    )


class PriceAlert(Base):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    game_id: Mapped[str] = mapped_column(String(255), ForeignKey("games.id"))
    target_price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    target_discount: Mapped[int | None] = mapped_column(Integer)
    region_code: Mapped[str] = mapped_column(String(5))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    triggered_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped["User"] = relationship()
    game: Mapped["Game"] = relationship()

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", "region_code"),
        Index("idx_price_alerts_active", "is_active"),
    )
