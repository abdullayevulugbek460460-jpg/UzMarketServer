import psycopg
from config import DATABASE_URL


SCHEMA = "uzmarket"


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL sozlanmagan")

    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:

            # =====================================================
            # SCHEMA
            # =====================================================

            cur.execute("""
                CREATE SCHEMA IF NOT EXISTS uzmarket
            """)

            # =====================================================
            # ADMINS
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.admins (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # USERS
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.users (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT UNIQUE NOT NULL,
                    password_hash TEXT,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # SELLER FIELDS
            # =====================================================

            cur.execute("""
                ALTER TABLE uzmarket.users
                ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'customer'
            """)

            cur.execute("""
                ALTER TABLE uzmarket.users
                ADD COLUMN IF NOT EXISTS seller_status TEXT DEFAULT NULL
            """)

            # =====================================================
            # CATEGORIES
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.categories (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    emoji TEXT DEFAULT '📦',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # BRANDS
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.brands (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # PRODUCTS
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.products (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    old_price INTEGER DEFAULT 0,
                    emoji TEXT DEFAULT '📦',
                    category TEXT DEFAULT 'Boshqa',
                    brand TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    stock INTEGER DEFAULT 0,
                    image TEXT DEFAULT '',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # BANNERS
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.banners (
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    subtitle TEXT DEFAULT '',
                    image TEXT DEFAULT '',
                    active BOOLEAN DEFAULT TRUE,
                    sort_order INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # CITIES
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.cities (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # ORDERS
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.orders (
                    id BIGSERIAL PRIMARY KEY,
                    order_code TEXT UNIQUE NOT NULL,
                    user_id BIGINT REFERENCES uzmarket.users(id),
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    products TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    status TEXT DEFAULT 'Jarayonda',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # DEFAULT CATEGORIES
            # =====================================================

            categories = [
                ("Barchasi", "🛍️"),
                ("Uy", "🏠"),
                ("Telefon", "📱"),
                ("Elektronika", "💻"),
                ("Kiyim", "👕"),
                ("Poyabzal", "👟"),
                ("Go‘zallik", "💄"),
                ("Oziq-ovqat", "🍎"),
            ]

            for name, emoji in categories:
                cur.execute("""
                    INSERT INTO uzmarket.categories (name, emoji)
                    VALUES (%s, %s)
                    ON CONFLICT (name) DO NOTHING
                """, (name, emoji))

            # =====================================================
            # DEFAULT CITIES
            # =====================================================

            cities = [
                "Andijon",
                "Toshkent",
                "Namangan",
                "Farg‘ona",
                "Samarqand",
                "Buxoro",
                "Navoiy",
                "Qarshi",
                "Jizzax",
                "Xorazm"
            ]

            for city in cities:
                cur.execute("""
                    INSERT INTO uzmarket.cities (name)
                    VALUES (%s)
                    ON CONFLICT (name) DO NOTHING
                """, (city,))

            conn.commit()


if __name__ == "__main__":
    init_db()
    print("OK: UzMarket database tayyor")
