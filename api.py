from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from functools import wraps
import random
import string

from config import PORT, JWT_SECRET
from database import get_connection, init_db

app = Flask(__name__)

SCHEMA = "uzmarket"


# =========================================================
# HELPERS
# =========================================================

def make_token(user_id, role="user"):
    return jwt.encode(
        {
            "user_id": user_id,
            "role": role
        },
        JWT_SECRET,
        algorithm="HS256"
    )


def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({
                "error": "Authorization kerak"
            }), 401

        token = header.replace("Bearer ", "", 1)

        try:
            data = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )

            request.user_id = data["user_id"]
            request.user_role = data.get("role", "user")

        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Token noto'g'ri yoki eskirgan"
            }), 401

        return f(*args, **kwargs)

    return decorated


def generate_order_code():
    chars = string.ascii_uppercase + string.digits
    return "UZ-" + "".join(
        random.choices(chars, k=8)
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return jsonify({
        "success": True,
        "app": "UzMarket Server",
        "version": "1.0.0",
        "schema": SCHEMA
    })


# =========================================================
# HEALTH
# =========================================================

@app.route("/health")
def health():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT current_database(), current_user
                """)

                db = cur.fetchone()

                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.schemata
                        WHERE schema_name = 'uzmarket'
                    )
                """)

                schema_exists = cur.fetchone()[0]

        return jsonify({
            "success": True,
            "database": "connected",
            "database_name": db[0],
            "database_user": db[1],
            "schema": "uzmarket",
            "schema_exists": schema_exists
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "database": "error",
            "message": str(e)
        }), 500


# =========================================================
# CATEGORIES
# =========================================================

@app.route("/categories", methods=["GET"])
def get_categories():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    emoji,
                    active
                FROM uzmarket.categories
                WHERE active = TRUE
                ORDER BY id
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "emoji": r[2],
            "active": r[3]
        }
        for r in rows
    ])


# =========================================================
# BRANDS
# =========================================================

@app.route("/brands", methods=["GET"])
def get_brands():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    active
                FROM uzmarket.brands
                WHERE active = TRUE
                ORDER BY name
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "active": r[2]
        }
        for r in rows
    ])


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products", methods=["GET"])
def get_products():

    category = request.args.get("category")
    brand = request.args.get("brand")
    search = request.args.get("search")

    query = """
        SELECT
            id,
            name,
            price,
            old_price,
            emoji,
            category,
            brand,
            description,
            stock,
            image
        FROM uzmarket.products
        WHERE active = TRUE
    """

    params = []

    if category and category != "Barchasi":
        query += " AND category = %s"
        params.append(category)

    if brand:
        query += " AND brand = %s"
        params.append(brand)

    if search:
        query += " AND name ILIKE %s"
        params.append("%" + search + "%")

    query += " ORDER BY id DESC"

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "price": r[2],
            "old_price": r[3],
            "emoji": r[4],
            "category": r[5],
            "brand": r[6],
            "description": r[7],
            "stock": r[8],
            "image": r[9]
        }
        for r in rows
    ])


# =========================================================
# SINGLE PRODUCT
# =========================================================

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    price,
                    old_price,
                    emoji,
                    category,
                    brand,
                    description,
                    stock,
                    image
                FROM uzmarket.products
                WHERE id = %s
                  AND active = TRUE
            """, (product_id,))

            r = cur.fetchone()

    if not r:
        return jsonify({
            "error": "Mahsulot topilmadi"
        }), 404

    return jsonify({
        "id": r[0],
        "name": r[1],
        "price": r[2],
        "old_price": r[3],
        "emoji": r[4],
        "category": r[5],
        "brand": r[6],
        "description": r[7],
        "stock": r[8],
        "image": r[9]
    })


# =========================================================
# BANNERS
# =========================================================

@app.route("/banners", methods=["GET"])
def get_banners():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    title,
                    subtitle,
                    image,
                    sort_order
                FROM uzmarket.banners
                WHERE active = TRUE
                ORDER BY sort_order, id
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "title": r[1],
            "subtitle": r[2],
            "image": r[3],
            "sort_order": r[4]
        }
        for r in rows
    ])


# =========================================================
# CITIES
# =========================================================

@app.route("/cities", methods=["GET"])
def get_cities():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    name
                FROM uzmarket.cities
                WHERE active = TRUE
                ORDER BY id
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1]
        }
        for r in rows
    ])


# =========================================================
# REGISTER
# =========================================================

@app.route("/auth/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not name or not phone or not password:
        return jsonify({
            "error": "name, phone va password kerak"
        }), 400

    if len(password) < 4:
        return jsonify({
            "error": "Parol kamida 4 ta belgidan iborat bo'lishi kerak"
        }), 400

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO uzmarket.users
                    (name, phone, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (
                    name,
                    phone,
                    password_hash
                ))

                user_id = cur.fetchone()[0]

            conn.commit()

    except Exception:
        return jsonify({
            "error": "Bu telefon raqami allaqachon ro'yxatdan o'tgan"
        }), 409

    token = make_token(user_id)

    return jsonify({
        "success": True,
        "user": {
            "id": user_id,
            "name": name,
            "phone": phone
        },
        "token": token
    }), 201


# =========================================================
# LOGIN
# =========================================================

@app.route("/auth/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    phone = str(data.get("phone", "")).strip()
    password = str(data.get("password", ""))

    if not phone or not password:
        return jsonify({
            "error": "phone va password kerak"
        }), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    phone,
                    password_hash
                FROM uzmarket.users
                WHERE phone = %s
            """, (phone,))

            user = cur.fetchone()

    if not user or not user[3]:
        return jsonify({
            "error": "Telefon yoki parol noto'g'ri"
        }), 401

    if not check_password_hash(user[3], password):
        return jsonify({
            "error": "Telefon yoki parol noto'g'ri"
        }), 401

    token = make_token(user[0])

    return jsonify({
        "success": True,
        "user": {
            "id": user[0],
            "name": user[1],
            "phone": user[2]
        },
        "token": token
    })


# =========================================================
# ME
# =========================================================

@app.route("/auth/me", methods=["GET"])
@auth_required
def me():

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    name,
                    phone,
                    created_at
                FROM uzmarket.users
                WHERE id = %s
            """, (request.user_id,))

            user = cur.fetchone()

    if not user:
        return jsonify({
            "error": "Foydalanuvchi topilmadi"
        }), 404

    return jsonify({
        "id": user[0],
        "name": user[1],
        "phone": user[2],
        "created_at": user[3]
    })


# =========================================================
# CREATE ORDER
# =========================================================

@app.route("/orders", methods=["POST"])
@auth_required
def create_order():

    data = request.get_json(silent=True) or {}

    customer_name = str(
        data.get("customer_name", "")
    ).strip()

    phone = str(
        data.get("phone", "")
    ).strip()

    address = str(
        data.get("address", "")
    ).strip()

    products = data.get("products")
    total = data.get("total")

    if not customer_name or not phone or not address:
        return jsonify({
            "error": "customer_name, phone va address kerak"
        }), 400

    if products is None:
        return jsonify({
            "error": "products kerak"
        }), 400

    try:
        total = int(total)
    except (TypeError, ValueError):
        return jsonify({
            "error": "total noto'g'ri"
        }), 400

    if total <= 0:
        return jsonify({
            "error": "total 0 dan katta bo'lishi kerak"
        }), 400

    order_code = generate_order_code()

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO uzmarket.orders
                (
                    order_code,
                    user_id,
                    customer_name,
                    phone,
                    address,
                    products,
                    total
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s)
                RETURNING
                    id,
                    created_at
            """, (
                order_code,
                request.user_id,
                customer_name,
                phone,
                str(products),
                address,
                total
            ))

            order_id, created_at = cur.fetchone()

        conn.commit()

    return jsonify({
        "success": True,
        "order": {
            "id": order_id,
            "order_code": order_code,
            "customer_name": customer_name,
            "phone": phone,
            "address": address,
            "products": products,
            "total": total,
            "status": "Jarayonda",
            "created_at": created_at
        }
    }), 201


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/orders", methods=["GET"])
@auth_required
def get_orders():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    order_code,
                    customer_name,
                    phone,
                    address,
                    products,
                    total,
                    status,
                    created_at
                FROM uzmarket.orders
                WHERE user_id = %s
                ORDER BY id DESC
            """, (request.user_id,))

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "order_code": r[1],
            "customer_name": r[2],
            "phone": r[3],
            "address": r[4],
            "products": r[5],
            "total": r[6],
            "status": r[7],
            "created_at": r[8]
        }
        for r in rows
    ])


# =========================================================
# SINGLE ORDER
# =========================================================

@app.route("/orders/<int:order_id>", methods=["GET"])
@auth_required
def get_order(order_id):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    order_code,
                    customer_name,
                    phone,
                    address,
                    products,
                    total,
                    status,
                    created_at
                FROM uzmarket.orders
                WHERE id = %s
                  AND user_id = %s
            """, (
                order_id,
                request.user_id
            ))

            r = cur.fetchone()

    if not r:
        return jsonify({
            "error": "Buyurtma topilmadi"
        }), 404

    return jsonify({
        "id": r[0],
        "order_code": r[1],
        "customer_name": r[2],
        "phone": r[3],
        "address": r[4],
        "products": r[5],
        "total": r[6],
        "status": r[7],
        "created_at": r[8]
    })


# =========================================================
# RUN
# =========================================================



# =========================================================
# ADMIN AUTH
# =========================================================

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({
                "error": "Admin Authorization kerak"
            }), 401

        token = header.replace("Bearer ", "", 1)

        try:
            data = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )

            if data.get("role") != "admin":
                return jsonify({
                    "error": "Admin huquqi kerak"
                }), 403

            request.admin_id = data["user_id"]

        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Admin token noto'g'ri"
            }), 401

        return f(*args, **kwargs)

    return decorated


# =========================================================
# ADMIN REGISTER
# =========================================================

@app.route("/admin/register", methods=["POST"])
def admin_register():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not username or not password:
        return jsonify({
            "error": "username va password kerak"
        }), 400

    if len(password) < 6:
        return jsonify({
            "error": "Admin paroli kamida 6 ta belgi bo'lishi kerak"
        }), 400

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO uzmarket.admins
                    (username, password_hash)
                    VALUES (%s, %s)
                    RETURNING id
                """, (
                    username,
                    password_hash
                ))

                admin_id = cur.fetchone()[0]

            conn.commit()

    except Exception:
        return jsonify({
            "error": "Bu admin username allaqachon mavjud"
        }), 409

    return jsonify({
        "success": True,
        "admin_id": admin_id,
        "message": "Admin yaratildi"
    }), 201


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["POST"])
def admin_login():

    data = request.get_json(silent=True) or {}

    username = str(
        data.get("username", "")
    ).strip()

    password = str(
        data.get("password", "")
    )

    if not username or not password:
        return jsonify({
            "error": "username va password kerak"
        }), 400

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    username,
                    password_hash,
                    active
                FROM uzmarket.admins
                WHERE username = %s
            """, (username,))

            admin = cur.fetchone()

    if not admin:
        return jsonify({
            "error": "Username yoki parol noto'g'ri"
        }), 401

    if not admin[3]:
        return jsonify({
            "error": "Admin faol emas"
        }), 403

    if not check_password_hash(
        admin[2],
        password
    ):
        return jsonify({
            "error": "Username yoki parol noto'g'ri"
        }), 401

    token = make_token(
        admin[0],
        "admin"
    )

    return jsonify({
        "success": True,
        "admin": {
            "id": admin[0],
            "username": admin[1]
        },
        "token": token
    })


# =========================================================
# ADMIN PRODUCTS - CREATE
# =========================================================

@app.route("/admin/products", methods=["POST"])
@admin_required
def admin_create_product():

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        return jsonify({
            "error": "name kerak"
        }), 400

    try:
        price = int(data.get("price", 0))
        old_price = int(data.get("old_price", 0))
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError):
        return jsonify({
            "error": "price, old_price yoki stock noto'g'ri"
        }), 400

    category = str(
        data.get("category", "Boshqa")
    ).strip()

    brand = str(
        data.get("brand", "")
    ).strip()

    emoji = str(
        data.get("emoji", "📦")
    )

    description = str(
        data.get("description", "")
    )

    image = str(
        data.get("image", "")
    )

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO uzmarket.products
                (
                    name,
                    price,
                    old_price,
                    emoji,
                    category,
                    brand,
                    description,
                    stock,
                    image
                )
                VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                name,
                price,
                old_price,
                emoji,
                category,
                brand,
                description,
                stock,
                image
            ))

            product_id = cur.fetchone()[0]

        conn.commit()

    return jsonify({
        "success": True,
        "product_id": product_id,
        "message": "Mahsulot qo'shildi"
    }), 201


# =========================================================
# ADMIN PRODUCTS - UPDATE
# =========================================================

@app.route("/admin/products/<int:product_id>", methods=["PUT"])
@admin_required
def admin_update_product(product_id):

    data = request.get_json(silent=True) or {}

    allowed = [
        "name",
        "price",
        "old_price",
        "emoji",
        "category",
        "brand",
        "description",
        "stock",
        "image",
        "active"
    ]

    fields = []
    values = []

    for field in allowed:

        if field in data:

            fields.append(
                f"{field} = %s"
            )

            values.append(
                data[field]
            )

    if not fields:
        return jsonify({
            "error": "Yangilanadigan maydon topilmadi"
        }), 400

    values.append(product_id)

    query = f"""
        UPDATE uzmarket.products
        SET {", ".join(fields)}
        WHERE id = %s
        RETURNING id
    """

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                query,
                values
            )

            result = cur.fetchone()

        conn.commit()

    if not result:
        return jsonify({
            "error": "Mahsulot topilmadi"
        }), 404

    return jsonify({
        "success": True,
        "message": "Mahsulot yangilandi"
    })


# =========================================================
# ADMIN PRODUCTS - DELETE
# =========================================================

@app.route("/admin/products/<int:product_id>", methods=["DELETE"])
@admin_required
def admin_delete_product(product_id):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                UPDATE uzmarket.products
                SET active = FALSE
                WHERE id = %s
                RETURNING id
            """, (product_id,))

            result = cur.fetchone()

        conn.commit()

    if not result:
        return jsonify({
            "error": "Mahsulot topilmadi"
        }), 404

    return jsonify({
        "success": True,
        "message": "Mahsulot o'chirildi"
    })


# =========================================================
# ADMIN CATEGORIES - CREATE
# =========================================================

@app.route("/admin/categories", methods=["POST"])
@admin_required
def admin_create_category():

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    emoji = str(
        data.get("emoji", "📦")
    )

    if not name:
        return jsonify({
            "error": "name kerak"
        }), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO uzmarket.categories
                    (name, emoji)
                    VALUES (%s, %s)
                    RETURNING id
                """, (
                    name,
                    emoji
                ))

                category_id = cur.fetchone()[0]

            conn.commit()

    except Exception:
        return jsonify({
            "error": "Bu kategoriya allaqachon mavjud"
        }), 409

    return jsonify({
        "success": True,
        "category_id": category_id
    }), 201


# =========================================================
# ADMIN BRANDS - CREATE
# =========================================================

@app.route("/admin/brands", methods=["POST"])
@admin_required
def admin_create_brand():

    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        return jsonify({
            "error": "name kerak"
        }), 400

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:

                cur.execute("""
                    INSERT INTO uzmarket.brands
                    (name)
                    VALUES (%s)
                    RETURNING id
                """, (name,))

                brand_id = cur.fetchone()[0]

            conn.commit()

    except Exception:
        return jsonify({
            "error": "Bu brand allaqachon mavjud"
        }), 409

    return jsonify({
        "success": True,
        "brand_id": brand_id
    }), 201


# =========================================================
# ADMIN BANNERS - CREATE
# =========================================================

@app.route("/admin/banners", methods=["POST"])
@admin_required
def admin_create_banner():

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "title kerak"
        }), 400

    subtitle = str(
        data.get("subtitle", "")
    )

    image = str(
        data.get("image", "")
    )

    try:
        sort_order = int(
            data.get("sort_order", 0)
        )
    except (TypeError, ValueError):
        sort_order = 0

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                INSERT INTO uzmarket.banners
                (
                    title,
                    subtitle,
                    image,
                    sort_order
                )
                VALUES
                (%s, %s, %s, %s)
                RETURNING id
            """, (
                title,
                subtitle,
                image,
                sort_order
            ))

            banner_id = cur.fetchone()[0]

        conn.commit()

    return jsonify({
        "success": True,
        "banner_id": banner_id
    }), 201

# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":
    init_db()

    app.run(
        host="0.0.0.0",
        port=PORT,
        debug=False
    )
