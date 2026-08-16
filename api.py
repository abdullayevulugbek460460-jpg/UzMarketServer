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

    except Exception as e:
        print("SELLER REGISTER ERROR:", repr(e))

        if getattr(e, "sqlstate", None) == "23505":
            return jsonify({
                "error": "Bu telefon raqami allaqachon ro'yxatdan o'tgan",
                "detail": str(e)
            }), 409

        return jsonify({
            "error": "Sotuvchi ro'yxatdan o'tishda server xatosi",
            "detail": str(e)
        }), 500

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
# SELLER REGISTER
# =========================================================

@app.route("/auth/seller/register", methods=["POST"])
def seller_register():

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
                    (name, phone, password_hash, role, seller_status)
                    VALUES (%s, %s, %s, 'seller', 'PENDING')
                    RETURNING id
                """, (
                    name,
                    phone,
                    password_hash
                ))

                user_id = cur.fetchone()[0]

            conn.commit()

    except Exception as e:
        print("SELLER REGISTER ERROR:", repr(e))

        if getattr(e, "sqlstate", None) == "23505":
            return jsonify({
                "error": "Bu telefon raqami allaqachon ro'yxatdan o'tgan",
                "detail": str(e)
            }), 409

        return jsonify({
            "error": "Sotuvchi ro'yxatdan o'tishda server xatosi",
            "detail": str(e)
        }), 500

    return jsonify({
        "success": True,
        "user": {
            "id": user_id,
            "name": name,
            "phone": phone,
            "role": "seller",
            "seller_status": "PENDING"
        },
        "message": "Sotuvchi arizasi yuborildi. Admin tasdig'i kutilmoqda."
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
                    password_hash,
                    role,
                    seller_status
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

    role = user[4] or "user"
    seller_status = user[5]

    if role == "seller" and seller_status != "APPROVED":
        return jsonify({
            "error": "Sotuvchi hali admin tomonidan tasdiqlanmagan"
        }), 403

    token = make_token(user[0], role)

    return jsonify({
        "success": True,
        "user": {
            "id": user[0],
            "name": user[1],
            "phone": user[2],
            "role": role,
            "seller_status": seller_status
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

    # products ichidan product_id larni topamiz.
    # Checkout hozir JSON obyektlarini \n bilan yuboryapti.
    import json

    product_ids = []

    try:
        if isinstance(products, list):
            for item in products:
                if isinstance(item, dict) and item.get("product_id"):
                    product_ids.append(int(item["product_id"]))

        elif isinstance(products, str):
            for line in products.splitlines():
                line = line.strip()
                if not line:
                    continue

                try:
                    item = json.loads(line)
                    if item.get("product_id"):
                        product_ids.append(int(item["product_id"]))
                except Exception:
                    pass
    except Exception:
        product_ids = []

    product_ids = list(dict.fromkeys(product_ids))

    order_seller_id = None

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Mahsulotlarning seller_id larini aniqlaymiz
            if product_ids:
                cur.execute("""
                    SELECT DISTINCT seller_id
                    FROM uzmarket.products
                    WHERE id = ANY(%s)
                      AND seller_id IS NOT NULL
                """, (product_ids,))

                seller_rows = cur.fetchall()

                seller_ids = [
                    int(row[0])
                    for row in seller_rows
                    if row[0] is not None
                ]

                # Barcha mahsulotlar bitta sellerga tegishli bo'lsa
                # order seller_id shu seller bo'ladi.
                if len(seller_ids) == 1:
                    order_seller_id = seller_ids[0]

            order_code = generate_order_code()

            cur.execute("""
                INSERT INTO uzmarket.orders
                (
                    order_code,
                    user_id,
                    customer_name,
                    phone,
                    address,
                    products,
                    total,
                    seller_id
                )
                VALUES
                (
                    %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id, created_at
            """, (
                order_code,
                request.user_id,
                customer_name,
                phone,
                address,
                str(products),
                total,
                order_seller_id
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
            "seller_id": order_seller_id,
            "status": "Jarayonda",
            "created_at": created_at.isoformat()
                if created_at else None
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
# ADMIN ORDERS
# =========================================================

@app.route("/admin/orders", methods=["GET"])
@admin_required
def admin_get_orders():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    order_code,
                    user_id,
                    customer_name,
                    phone,
                    address,
                    products,
                    total,
                    status,
                    created_at
                FROM uzmarket.orders
                ORDER BY id DESC
            """)
            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "order_code": r[1],
            "user_id": r[2],
            "customer_name": r[3],
            "phone": r[4],
            "address": r[5],
            "products": r[6],
            "total": r[7],
            "status": r[8],
            "created_at": r[9].isoformat() if r[9] else None
        }
        for r in rows
    ])


@app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
@admin_required
def admin_update_order_status(order_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()

    allowed = {
        "Jarayonda",
        "Tasdiqlandi",
        "Tayyorlanmoqda",
        "Yo‘lda",
        "Yetkazildi",
        "Bekor qilindi"
    }

    if status not in allowed:
        return jsonify({
            "error": "Noto‘g‘ri status",
            "allowed": list(allowed)
        }), 400

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE uzmarket.orders
                SET status = %s
                WHERE id = %s
                RETURNING
                    id,
                    order_code,
                    status
            """, (status, order_id))

            order = cur.fetchone()
            conn.commit()

    if not order:
        return jsonify({
            "error": "Buyurtma topilmadi"
        }), 404

    return jsonify({
        "success": True,
        "message": "Buyurtma statusi yangilandi",
        "order": {
            "id": order[0],
            "order_code": order[1],
            "status": order[2]
        }
    })


# =========================================================
# ADMIN SELLERS - LIST
# =========================================================

@app.route("/admin/sellers", methods=["GET"])
@admin_required
def admin_get_sellers():

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    id,
                    name,
                    phone,
                    role,
                    seller_status,
                    created_at
                FROM uzmarket.users
                WHERE role = 'seller'
                ORDER BY id DESC
            """)

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "name": r[1],
            "phone": r[2],
            "role": r[3],
            "seller_status": r[4],
            "created_at": r[5].isoformat() if r[5] else None
        }
        for r in rows
    ])


# =========================================================
# ADMIN SELLER - APPROVE
# =========================================================

@app.route("/admin/sellers/<int:user_id>/approve", methods=["POST"])
@admin_required
def admin_approve_seller(user_id):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                UPDATE uzmarket.users
                SET seller_status = 'APPROVED'
                WHERE id = %s
                  AND role = 'seller'
                RETURNING id, name, phone
            """, (user_id,))

            seller = cur.fetchone()

        conn.commit()

    if not seller:
        return jsonify({
            "error": "Sotuvchi topilmadi"
        }), 404

    return jsonify({
        "success": True,
        "message": "Sotuvchi tasdiqlandi",
        "seller": {
            "id": seller[0],
            "name": seller[1],
            "phone": seller[2],
            "seller_status": "APPROVED"
        }
    })


# =========================================================
# ADMIN SELLER - REJECT
# =========================================================

@app.route("/admin/sellers/<int:user_id>/reject", methods=["POST"])
@admin_required
def admin_reject_seller(user_id):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                UPDATE uzmarket.users
                SET seller_status = 'REJECTED'
                WHERE id = %s
                  AND role = 'seller'
                RETURNING id, name, phone
            """, (user_id,))

            seller = cur.fetchone()

        conn.commit()

    if not seller:
        return jsonify({
            "error": "Sotuvchi topilmadi"
        }), 404

    return jsonify({
        "success": True,
        "message": "Sotuvchi rad etildi",
        "seller": {
            "id": seller[0],
            "name": seller[1],
            "phone": seller[2],
            "seller_status": "REJECTED"
        }
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

init_db()

# =========================================================
# SELLER PRODUCTS
# =========================================================

def seller_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get("Authorization", "")

        if not header.startswith("Bearer "):
            return jsonify({
                "error": "Seller Authorization kerak"
            }), 401

        token = header.replace("Bearer ", "", 1)

        try:
            data = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=["HS256"]
            )

            if data.get("role") != "seller":
                return jsonify({
                    "error": "Faqat sotuvchi uchun"
                }), 403

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id, name, phone, seller_status
                        FROM uzmarket.users
                        WHERE id = %s
                          AND role = 'seller'
                    """, (data.get("user_id"),))

                    seller = cur.fetchone()

            if not seller:
                return jsonify({
                    "error": "Sotuvchi topilmadi"
                }), 404

            if seller[3] != "APPROVED":
                return jsonify({
                    "error": "Sotuvchi hali admin tomonidan tasdiqlanmagan"
                }), 403

            request.seller_id = seller[0]
            request.seller_name = seller[1]

        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Seller token noto'g'ri"
            }), 401

        return f(*args, **kwargs)

    return decorated



@app.route("/seller/orders", methods=["GET"])
@seller_required
def seller_get_orders():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    order_code,
                    user_id,
                    customer_name,
                    phone,
                    address,
                    products,
                    total,
                    status,
                    created_at
                FROM uzmarket.orders
                WHERE seller_id = %s
                ORDER BY id DESC
            """, (request.seller_id,))

            rows = cur.fetchall()

    return jsonify([
        {
            "id": r[0],
            "order_code": r[1],
            "user_id": r[2],
            "customer_name": r[3],
            "phone": r[4],
            "address": r[5],
            "products": r[6],
            "total": r[7],
            "status": r[8],
            "created_at": r[9].isoformat()
                if r[9] else None
        }
        for r in rows
    ])

# =========================================================
# SELLER ORDERS STATUS
# =========================================================

@app.route("/seller/orders/<int:order_id>/status", methods=["POST"])
@seller_required
def seller_update_order_status(order_id):
    data = request.get_json(silent=True) or {}
    status = str(data.get("status", "")).strip()

    allowed_statuses = [
        "Jarayonda",
        "Qabul qilindi",
        "Tayyorlanmoqda",
        "Yuborildi",
        "Yetkazildi",
        "Yakunlandi",
        "Bekor qilindi"
    ]

    if status not in allowed_statuses:
        return jsonify({
            "error": "Noto'g'ri status",
            "allowed": allowed_statuses
        }), 400

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Buyurtmani olamiz va sellerga tegishliligini tekshiramiz
            cur.execute("""
                SELECT
                    id,
                    order_code,
                    products,
                    total,
                    status
                FROM uzmarket.orders
                WHERE id = %s
                  AND seller_id = %s
                FOR UPDATE
            """, (
                order_id,
                request.seller_id
            ))

            order = cur.fetchone()

            if not order:
                return jsonify({
                    "error": "Buyurtma topilmadi"
                }), 404

            old_status = order[4]

            # Yakunlangan buyurtmani qayta yakunlashga yo'l yo'q.
            if old_status == "Yakunlandi":
                return jsonify({
                    "error": "Buyurtma allaqachon yakunlangan",
                    "order": {
                        "id": order[0],
                        "order_code": order[1],
                        "status": old_status
                    }
                }), 400

            # Yakunlashdan oldin Yetkazildi bo'lishi kerak.
            if status == "Yakunlandi" and old_status != "Yetkazildi":
                return jsonify({
                    "error": "Buyurtmani faqat 'Yetkazildi' holatidan keyin yakunlash mumkin"
                }), 400

            # Statusni o'zgartiramiz
            cur.execute("""
                UPDATE uzmarket.orders
                SET status = %s
                WHERE id = %s
                  AND seller_id = %s
                RETURNING id, order_code, status
            """, (
                status,
                order_id,
                request.seller_id
            ))

            updated = cur.fetchone()

            if not updated:
                conn.rollback()
                return jsonify({
                    "error": "Buyurtma yangilanmadi"
                }), 400

            stock_updated = 0

            # FAQAT Yakunlandi bo'lganda ombordagi qoldiqni kamaytiramiz.
            if status == "Yakunlandi":

                import json

                try:
                    products_data = json.loads(order[2])
                except Exception:
                    products_data = []

                if isinstance(products_data, dict):
                    products_data = [products_data]

                for item in products_data:

                    if not isinstance(item, dict):
                        continue

                    try:
                        product_id = int(
                            item.get("product_id", 0)
                        )
                        quantity = int(
                            item.get("quantity", 0)
                        )
                    except (TypeError, ValueError):
                        continue

                    if product_id <= 0 or quantity <= 0:
                        continue

                    # Faqat shu sellerning mahsuloti kamayadi.
                    cur.execute("""
                        UPDATE uzmarket.products
                        SET stock = GREATEST(
                            0,
                            COALESCE(stock, 0) - %s
                        )
                        WHERE id = %s
                          AND seller_id = %s
                        RETURNING id
                    """, (
                        quantity,
                        product_id,
                        request.seller_id
                    ))

                    if cur.fetchone():
                        stock_updated += quantity

            conn.commit()

            return jsonify({
                "success": True,
                "message": (
                    "Buyurtma yakunlandi"
                    if status == "Yakunlandi"
                    else "Buyurtma holati yangilandi"
                ),
                "stock_updated": stock_updated,
                "order": {
                    "id": updated[0],
                    "order_code": updated[1],
                    "status": updated[2]
                }
            })


@app.route("/seller/products", methods=["GET"])
@seller_required
def seller_get_products():

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
                    image,
                    active,
                    created_at
                FROM uzmarket.products
                WHERE seller_id = %s
                ORDER BY id DESC
            """, (request.seller_id,))

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
            "image": r[9],
            "active": r[10],
            "created_at": r[11].isoformat() if r[11] else None
        }
        for r in rows
    ])


@app.route("/seller/products", methods=["POST"])
@seller_required
def seller_create_product():

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

    if price <= 0:
        return jsonify({
            "error": "price 0 dan katta bo'lishi kerak"
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
                    seller_id,
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
                (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                RETURNING id
            """, (
                request.seller_id,
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


@app.route("/seller/products/<int:product_id>", methods=["PUT"])
@seller_required
def seller_update_product(product_id):

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
                field + " = %s"
            )

            values.append(
                data[field]
            )

    if not fields:
        return jsonify({
            "error": "O'zgartiriladigan ma'lumot yo'q"
        }), 400

    values.append(product_id)
    values.append(request.seller_id)

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute(
                """
                UPDATE uzmarket.products
                SET
                """ + ", ".join(fields) + """
                WHERE id = %s
                  AND seller_id = %s
                RETURNING id, name
                """,
                tuple(values)
            )

            product = cur.fetchone()

            conn.commit()

    if not product:
        return jsonify({
            "error": "Mahsulot topilmadi yoki sizga tegishli emas"
        }), 404

    return jsonify({
        "success": True,
        "message": "Mahsulot yangilandi",
        "product": {
            "id": product[0],
            "name": product[1]
        }
    })


@app.route("/seller/products/<int:product_id>", methods=["DELETE"])
@seller_required
def seller_delete_product(product_id):

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                DELETE FROM uzmarket.products
                WHERE id = %s
                  AND seller_id = %s
                RETURNING id
            """, (
                product_id,
                request.seller_id
            ))

            product = cur.fetchone()

            conn.commit()

    if not product:
        return jsonify({
            "error": "Mahsulot topilmadi yoki sizga tegishli emas"
        }), 404

    return jsonify({
        "success": True,
        "message": "Mahsulot o'chirildi",
        "product_id": product[0]
    })


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
