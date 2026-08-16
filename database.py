import psycopg
from config import DATABASE_URL


SCHEMA = "uzmarket"


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL sozlanmagan")

    return psycopg.connect(DATABASE_URL, prepare_threshold=None)


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
                    seller_id BIGINT REFERENCES uzmarket.users(id),
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
            # PRODUCT SELLER
            # =====================================================
            cur.execute("""
                ALTER TABLE uzmarket.products
                ADD COLUMN IF NOT EXISTS seller_id BIGINT
                REFERENCES uzmarket.users(id)
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
                    seller_id BIGINT REFERENCES uzmarket.users(id),
                    status TEXT DEFAULT 'Jarayonda',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            # =====================================================
            # ORDER LOCATION
            # =====================================================
            cur.execute("""
                ALTER TABLE uzmarket.orders
                ADD COLUMN IF NOT EXISTS latitude DOUBLE PRECISION
            """)

            cur.execute("""
                ALTER TABLE uzmarket.orders
                ADD COLUMN IF NOT EXISTS longitude DOUBLE PRECISION
            """)

            # =====================================================
            # ORDERS SELLER MIGRATION
            # =====================================================
            cur.execute("""
                ALTER TABLE uzmarket.orders
                ADD COLUMN IF NOT EXISTS seller_id
                BIGINT REFERENCES uzmarket.users(id)
            """)

            # =====================================================
            # ORDER COMPLETION / STOCK MIGRATION
            # =====================================================
            cur.execute("""
                ALTER TABLE uzmarket.orders
                ADD COLUMN IF NOT EXISTS stock_deducted BOOLEAN DEFAULT FALSE
            """)

            cur.execute("""
                ALTER TABLE uzmarket.orders
                ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ
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


            # =====================================================
            # FOOD DELIVERY
            # =====================================================

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.food_restaurants (
                    id BIGSERIAL PRIMARY KEY,
                    owner_id BIGINT REFERENCES uzmarket.users(id),
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    description TEXT DEFAULT '',
                    logo TEXT DEFAULT '',
                    delivery_price INTEGER DEFAULT 0,
                    min_order INTEGER DEFAULT 0,
                    is_open BOOLEAN DEFAULT FALSE,
                    approved BOOLEAN DEFAULT FALSE,
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.food_categories (
                    id BIGSERIAL PRIMARY KEY,
                    restaurant_id BIGINT
                        REFERENCES uzmarket.food_restaurants(id)
                        ON DELETE CASCADE,
                    name TEXT NOT NULL,
                    emoji TEXT DEFAULT '🍽️',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    UNIQUE(restaurant_id, name)
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.food_menu (
                    id BIGSERIAL PRIMARY KEY,
                    restaurant_id BIGINT
                        REFERENCES uzmarket.food_restaurants(id)
                        ON DELETE CASCADE,
                    category_id BIGINT
                        REFERENCES uzmarket.food_categories(id)
                        ON DELETE SET NULL,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    price INTEGER NOT NULL,
                    image TEXT DEFAULT '',
                    available BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.food_orders (
                    id BIGSERIAL PRIMARY KEY,
                    order_code TEXT UNIQUE NOT NULL,
                    user_id BIGINT REFERENCES uzmarket.users(id),
                    restaurant_id BIGINT
                        REFERENCES uzmarket.food_restaurants(id),
                    customer_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    address TEXT NOT NULL,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    subtotal INTEGER NOT NULL DEFAULT 0,
                    delivery_price INTEGER NOT NULL DEFAULT 0,
                    total INTEGER NOT NULL DEFAULT 0,
                    status TEXT DEFAULT 'Yangi',
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    completed_at TIMESTAMPTZ
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS uzmarket.food_order_items (
                    id BIGSERIAL PRIMARY KEY,
                    order_id BIGINT
                        REFERENCES uzmarket.food_orders(id)
                        ON DELETE CASCADE,
                    menu_id BIGINT
                        REFERENCES uzmarket.food_menu(id),
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    total INTEGER NOT NULL DEFAULT 0
                )
            """)

            # Default food categories
            food_categories = [
                ("🍔", "Burger"),
                ("🍕", "Pitsa"),
                ("🌯", "Lavash"),
                ("🍗", "Fast-food"),
                ("🍲", "Milliy taomlar"),
                ("🥗", "Salatlar"),
                ("🍟", "Fri va gazaklar"),
                ("🥤", "Ichimliklar")
            ]

            # Categories are created per restaurant when the restaurant
            # creates its menu. No global restaurant-specific categories
            # are inserted here.

            conn.commit()


if __name__ == "__main__":
    init_db()
    print("OK: UzMarket database tayyor")
