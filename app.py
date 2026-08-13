from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "book_store"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "root"
app.config["MYSQL_DB"] = "book_store"

def get_db_connection():
    return pymysql.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        database=app.config["MYSQL_DB"],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def initialize_database():
    print("Initializing database...")
    # 1. Connect to MySQL server to create DB if not exists
    connection = pymysql.connect(
        host=app.config["MYSQL_HOST"],
        user=app.config["MYSQL_USER"],
        password=app.config["MYSQL_PASSWORD"],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['MYSQL_DB']};")
        connection.commit()
    finally:
        connection.close()

    # 2. Connect to the DB to create tables and seed
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Create Users Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'User',
                    shipping_address TEXT DEFAULT NULL,
                    avatar MEDIUMTEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Create Categories Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Create Books Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    category_name VARCHAR(255) NOT NULL,
                    price DECIMAL(10, 2) NOT NULL,
                    original_price DECIMAL(10, 2) DEFAULT NULL,
                    img LONGTEXT,
                    book_condition VARCHAR(50) DEFAULT 'new',
                    condition_description VARCHAR(255) DEFAULT NULL,
                    additional_notes TEXT DEFAULT NULL,
                    seller_id INT DEFAULT NULL,
                    approved BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (seller_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Create Orders Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    user_id INT DEFAULT NULL,
                    total_amount DECIMAL(10, 2) NOT NULL,
                    payment_method VARCHAR(100) NOT NULL,
                    status VARCHAR(50) DEFAULT 'Processing',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Create Order Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS order_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    order_id INT NOT NULL,
                    book_id INT DEFAULT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    price DECIMAL(10, 2) NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Create Cart Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cart_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    book_id INT NOT NULL,
                    quantity INT NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY user_book_cart (user_id, book_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Create Wishlist Items Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wishlist_items (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    book_id INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY user_book_wishlist (user_id, book_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            # Seed default categories
            categories = ["Fiction", "Programming", "Science", "Business", "Biography"]
            for cat in categories:
                cursor.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (cat,))

            # Seed default users
            admin_pwd = generate_password_hash("admin123")
            user_pwd = generate_password_hash("user123")
            cursor.execute(
                "INSERT IGNORE INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("Admin", "admin@bookbazar.com", admin_pwd, "Admin")
            )
            cursor.execute(
                "INSERT IGNORE INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                ("User", "user@gmail.com", user_pwd, "User")
            )

            # Seed Books
            initial_books = [
                {
                    "title": "Atomic Habits",
                    "author": "James Clear",
                    "price": 499.00,
                    "img": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=300",
                    "condition": "new",
                    "description": "An easy & proven way to build good habits & break bad ones. Tiny Changes, Remarkable Results.",
                    "category": "Business"
                },
                {
                    "title": "Deep Work",
                    "author": "Cal Newport",
                    "price": 399.00,
                    "img": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=300",
                    "condition": "new",
                    "description": "Rules for Focused Success in a Distracted World. Master difficult skills quickly and produce better results in less time.",
                    "category": "Programming"
                },
                {
                    "title": "Rich Dad Poor Dad",
                    "author": "Robert Kiyosaki",
                    "price": 299.00,
                    "img": "https://images.unsplash.com/photo-1543002588-bfa74002ed7e?w=300",
                    "condition": "new",
                    "description": "What the Rich Teach Their Kids About Money That the Poor and Middle Class Do Not!",
                    "category": "Business"
                },
                {
                    "title": "The Psychology of Money",
                    "author": "Morgan Housel",
                    "price": 599.00,
                    "img": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?w=300",
                    "condition": "new",
                    "description": "Timeless lessons on wealth, greed, and happiness. Doing well with money isn't necessarily about what you know. It's about how you behave.",
                    "category": "Business"
                },
                {
                    "title": "The Alchemist",
                    "author": "Paulo Coelho",
                    "price": 149.00,
                    "img": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=300",
                    "condition": "pre-loved",
                    "description": "A beautiful story about following your dreams. Highly inspiring fable about a shepherd boy who travels in search of worldly treasures.",
                    "category": "Fiction"
                },
                {
                    "title": "Zero to One",
                    "author": "Peter Thiel",
                    "price": 199.00,
                    "img": "https://images.unsplash.com/photo-1531988042231-d39a9cc12a9a?w=300",
                    "condition": "pre-loved",
                    "description": "Notes on Startups, or How to Build the Future. Learn how to discover new ways of creating value to go from 0 to 1.",
                    "category": "Business"
                },
                {
                    "title": "Thinking, Fast and Slow",
                    "author": "Daniel Kahneman",
                    "price": 249.00,
                    "img": "https://images.unsplash.com/photo-1495640388908-05fa85288e61?w=300",
                    "condition": "pre-loved",
                    "description": "A deep exploration of the two systems that drive our way of thinking: System 1 (fast/intuitive) and System 2 (slow/logical).",
                    "category": "Science"
                },
                {
                    "title": "Steve Jobs",
                    "author": "Walter Isaacson",
                    "price": 299.00,
                    "img": "https://images.unsplash.com/photo-1541963463532-d68292c34b19?w=300",
                    "condition": "pre-loved",
                    "description": "The exclusive biography of the creative entrepreneur who revolutionized the technology industry. Based on more than forty interviews.",
                    "category": "Biography"
                }
            ]

            for book in initial_books:
                cursor.execute("SELECT id FROM books WHERE title = %s", (book["title"],))
                if not cursor.fetchone():
                    cursor.execute(
                        """INSERT INTO books 
                        (title, author, category_name, price, img, book_condition, condition_description, approved) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)""",
                        (book["title"], book["author"], book["category"], book["price"], book["img"], book["condition"], book["description"])
                    )

        conn.commit()
        print("Database checked and initialized successfully!")
    except Exception as e:
        conn.rollback()
        print(f"Error checking/initializing database: {e}")
    finally:
        conn.close()

# ==========================
# SECURITY & ROUTING MIDDLEWARE
# ==========================

@app.before_request
def check_user_access():
    endpoint = request.endpoint
    if not endpoint:
        return

    # 1. Protect Admin routes (except admin_login) from non-Admin users
    if endpoint.startswith("admin_") and endpoint != "admin_login":
        if session.get("user") != "Admin":
            return redirect(url_for("admin_login"))

    # 2. Restrict logged-in Admin from accessing non-Admin/storefront pages
    if session.get("user") == "Admin":
        admin_allowed = [
            "admin_dashboard",
            "admin_books",
            "admin_add_book",
            "admin_edit_book",
            "admin_categories",
            "admin_add_category",
            "admin_edit_category",
            "admin_delete_category",
            "admin_orders",
            "admin_users",
            "admin_sellers",
            "admin_reports",
            "admin_settings",
            "logout",
            "static",
            "update_avatar_api"
        ]
        if endpoint not in admin_allowed and not endpoint.startswith("api_"):
            return redirect(url_for("admin_dashboard"))

# ==========================
# HOME
# ==========================


@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# BOOKS
# ==========================

@app.route("/books")
def books():
    categories_list = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM categories")
            categories_list = [row["name"] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error fetching categories for books: {e}")
    return render_template("books.html", categories=categories_list)


@app.route("/book/<int:id>")
def book_details(id):
    return render_template("book_details.html", id=id)


# ==========================
# CATEGORIES
# ==========================

@app.route("/categories")
def categories():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.name, COUNT(b.id) as book_count
                FROM categories c
                LEFT JOIN books b ON c.name = b.category_name AND b.approved = TRUE
                GROUP BY c.id, c.name
            """)
            categories_list = cursor.fetchall()
        conn.close()
        return render_template("categories.html", categories=categories_list)
    except Exception as e:
        return f"Database error: {e}"


# ==========================
# SELL BOOK
# ==========================

@app.route("/sell-book")
def sell_book():
    categories_list = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM categories")
            categories_list = [row["name"] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error fetching categories for sell-book: {e}")
    return render_template("user/sell_book.html", categories=categories_list)


# ==========================
# CART
# ==========================

@app.route("/cart")
def cart():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/cart.html")


# ==========================
# WISHLIST
# ==========================

@app.route("/wishlist")
def wishlist():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/wishlist.html")


# ==========================
# LOGIN
# ==========================

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user" in session:
        if session["user"] == "Admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("profile"))

    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user"] = user["role"]
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                session["user_avatar"] = user.get("avatar")
                if user["role"] == "Admin":
                    return redirect(url_for("admin_dashboard"))
                else:
                    return redirect(url_for("profile"))
            else:
                error = "Invalid Email or Password"
        except Exception as e:
            error = f"Database error: {e}"

    registered = request.args.get("registered")
    return render_template("user/login.html", error=error, registered=registered)


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if "user" in session:
        if session["user"] == "Admin":
            return redirect(url_for("admin_dashboard"))
        else:
            return redirect(url_for("profile"))

    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s AND role = 'Admin'", (email,))
                user = cursor.fetchone()
            conn.close()

            if user and check_password_hash(user["password"], password):
                session["user"] = "Admin"
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                session["user_email"] = user["email"]
                session["user_avatar"] = user.get("avatar")
                return redirect(url_for("admin_dashboard"))
            else:
                error = "Invalid Admin Credentials"
        except Exception as e:
            error = f"Database error: {e}"

    return render_template("admin/login.html", error=error)


# ==========================
# REGISTER
# ==========================

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        if not (name and email and password):
            error = "All fields are required"
        else:
            hashed_pwd = generate_password_hash(password)
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    # Check if email exists
                    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                    if cursor.fetchone():
                        error = "Email address already registered"
                    else:
                        cursor.execute(
                            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, 'User')",
                            (name, email, hashed_pwd)
                        )
                        conn.commit()
                        conn.close()
                        return redirect(url_for("login", registered="true"))
                conn.close()
            except Exception as e:
                error = f"Database error: {e}"

    return render_template("user/register.html", error=error)


# ==========================
# PROFILE
# ==========================

@app.route("/profile")
def profile():
    if "user" not in session:
        return redirect(url_for("login"))
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name, avatar FROM users WHERE id = %s", (session.get("user_id"),))
            user = cursor.fetchone()
        conn.close()
        if user:
            session["user_name"] = user["name"]
            session["user_avatar"] = user["avatar"]
    except Exception as e:
        print(f"Error updating profile session: {e}")
    return render_template("user/profile.html")


@app.route("/profile/details")
def profile_details():
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name, shipping_address, avatar FROM users WHERE id = %s", (session.get("user_id"),))
            user = cursor.fetchone()
        conn.close()
        address = user["shipping_address"] if user else ""
        if user:
            session["user_name"] = user["name"]
            session["user_avatar"] = user["avatar"]
    except Exception as e:
        print(f"Error fetching profile details: {e}")
        address = ""

    success = request.args.get("success")
    return render_template("user/profile_details.html", address=address, success=success)


@app.route("/update-profile", methods=["POST"])
def update_profile():
    if "user" not in session:
        return redirect(url_for("login"))

    name = request.form.get("name")
    shipping_address = request.form.get("shipping_address")

    if not name:
        return "Name is required", 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET name = %s, shipping_address = %s WHERE id = %s",
                (name, shipping_address, session.get("user_id"))
            )
        conn.commit()
        conn.close()

        # Sync updated name back to the session
        session["user_name"] = name
        return redirect(url_for("profile_details", success="true"))
    except Exception as e:
        return f"Database error: {e}", 500


@app.route("/api/profile/avatar", methods=["POST"])
def update_avatar_api():
    if "user" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        avatar = data.get("avatar")

        if not avatar:
            return jsonify({"error": "No avatar data provided"}), 400

        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET avatar = %s WHERE id = %s", (avatar, session.get("user_id")))
        conn.commit()
        conn.close()

        # Save in session for instant display
        session["user_avatar"] = avatar
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================
# CONTACT
# ==========================

@app.route("/contact")
def contact():
    return render_template("contact.html")


# ==========================
# ADMIN
# ==========================

# ==========================
# ADMIN
# ==========================

@app.route("/admin")
def admin_dashboard():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # 1. Total Books Count
            cursor.execute("SELECT COUNT(*) as count FROM books")
            total_books = cursor.fetchone()["count"]

            # 2. Total Orders Count
            cursor.execute("SELECT COUNT(*) as count FROM orders")
            total_orders = cursor.fetchone()["count"]

            # 3. Active Users Count (non-Admins)
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE role = 'User'")
            total_users = cursor.fetchone()["count"]

            # 4. Total Revenue
            cursor.execute("SELECT SUM(total_amount) as revenue FROM orders")
            res_rev = cursor.fetchone()["revenue"]
            total_revenue = float(res_rev) if res_rev is not None else 0.0

            # 5. Recent Orders (limit 5)
            cursor.execute("""
                SELECT o.order_number, u.name as customer_name,
                       (SELECT b.title FROM order_items oi 
                        JOIN books b ON oi.book_id = b.id 
                        WHERE oi.order_id = o.id LIMIT 1) as book_title,
                       o.total_amount, o.status
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
                LIMIT 5
            """)
            recent_orders = cursor.fetchall()

        conn.close()
        return render_template(
            "admin/dashboard.html",
            total_books=total_books,
            total_orders=total_orders,
            total_users=total_users,
            total_revenue=total_revenue,
            recent_orders=recent_orders
        )
    except Exception as e:
        return f"Database error: {e}"


@app.route("/admin/books")
def admin_books():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
    return render_template("admin/books.html")


@app.route("/admin/add-book", methods=["GET", "POST"])
def admin_add_book():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    error = None
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        category_name = request.form.get("category_name")
        price = request.form.get("price")
        book_condition = request.form.get("book_condition", "new").lower()
        img = request.form.get("img")
        description = request.form.get("description")
        
        if not (title and author and category_name and price):
            error = "Title, Author, Category, and Price are required"
        else:
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO books (title, author, category_name, price, book_condition, img, condition_description, seller_id, approved) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                        """,
                        (title, author, category_name, float(price), book_condition, img, description, session.get("user_id"))
                    )
                conn.commit()
                conn.close()
                return redirect(url_for("admin_books", success="true"))
            except Exception as e:
                error = f"Database error: {e}"
                
    # Load categories for the dropdown list
    categories_list = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM categories")
            categories_list = [row["name"] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error fetching categories: {e}")
        
    return render_template("admin/add_book.html", categories=categories_list, error=error)


@app.route("/admin/edit-book/<int:id>", methods=["GET", "POST"])
def admin_edit_book(id):
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    error = None
    book = None
    
    # 1. Fetch the book to edit
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT b.*, u.name AS seller_name, u.email AS seller_email 
                FROM books b 
                LEFT JOIN users u ON b.seller_id = u.id 
                WHERE b.id = %s
            """, (id,))
            book = cursor.fetchone()
        conn.close()
    except Exception as e:
        error = f"Database error: {e}"
        
    if not book:
        return "Book not found", 404
        
    # 2. Handle post update
    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        category_name = request.form.get("category_name")
        price = request.form.get("price")
        book_condition = request.form.get("book_condition", "new").lower()
        img = request.form.get("img") or book["img"] # preserve old image if not uploaded
        description = request.form.get("description")
        
        if not (title and author and category_name and price):
            error = "Title, Author, Category, and Price are required"
        else:
            try:
                conn = get_db_connection()
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE books 
                        SET title = %s, author = %s, category_name = %s, price = %s, book_condition = %s, img = %s, condition_description = %s
                        WHERE id = %s
                        """,
                        (title, author, category_name, float(price), book_condition, img, description, id)
                    )
                conn.commit()
                conn.close()
                return redirect(url_for("admin_books", success="true"))
            except Exception as e:
                error = f"Database error: {e}"
                
    # 3. Load categories for dropdown
    categories_list = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM categories")
            categories_list = [row["name"] for row in cursor.fetchall()]
        conn.close()
    except Exception as e:
        print(f"Error fetching categories: {e}")
        
    return render_template("admin/edit_book.html", book=book, categories=categories_list, error=error)


@app.route("/admin/categories")
def admin_categories():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.id, c.name, COUNT(b.id) as book_count
                FROM categories c
                LEFT JOIN books b ON c.name = b.category_name
                GROUP BY c.id, c.name
            """)
            categories_list = cursor.fetchall()
        conn.close()
        return render_template("admin/categories.html", categories=categories_list)
    except Exception as e:
        return f"Database error: {e}"


@app.route("/admin/categories/add", methods=["POST"])
def admin_add_category():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    name = request.form.get("name")
    if not name:
        return redirect(url_for("admin_categories", error="Category name is required"))

    name = name.strip()
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
            if cursor.fetchone():
                conn.close()
                return redirect(url_for("admin_categories", error=f"Category '{name}' already exists"))

            cursor.execute("INSERT INTO categories (name) VALUES (%s)", (name,))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_categories", added="true"))
    except Exception as e:
        return redirect(url_for("admin_categories", error=f"Database error: {e}"))


@app.route("/admin/categories/edit/<int:id>", methods=["POST"])
def admin_edit_category(id):
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    name = request.form.get("name")
    if not name:
        return redirect(url_for("admin_categories", error="Category name is required"))

    name = name.strip()
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT name FROM categories WHERE id = %s", (id,))
            old_category = cursor.fetchone()
            if not old_category:
                conn.close()
                return redirect(url_for("admin_categories", error="Category not found"))

            old_name = old_category["name"]

            cursor.execute("SELECT id FROM categories WHERE name = %s AND id != %s", (name, id))
            if cursor.fetchone():
                conn.close()
                return redirect(url_for("admin_categories", error=f"Category '{name}' already exists"))

            cursor.execute("UPDATE categories SET name = %s WHERE id = %s", (name, id))
            cursor.execute("UPDATE books SET category_name = %s WHERE category_name = %s", (name, old_name))

        conn.commit()
        conn.close()
        return redirect(url_for("admin_categories", success="true"))
    except Exception as e:
        return redirect(url_for("admin_categories", error=f"Database error: {e}"))


@app.route("/admin/categories/delete/<int:id>", methods=["POST"])
def admin_delete_category(id):
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM categories WHERE id = %s", (id,))
        conn.commit()
        conn.close()
        return redirect(url_for("admin_categories", deleted="true"))
    except Exception as e:
        return redirect(url_for("admin_categories", error=f"Database error: {e}"))



@app.route("/admin/orders")
def admin_orders():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*, u.name as customer_name,
                       (SELECT GROUP_CONCAT(b.title SEPARATOR ', ') 
                        FROM order_items oi 
                        JOIN books b ON oi.book_id = b.id 
                        WHERE oi.order_id = o.id) as book_titles
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
            """)
            orders_list = cursor.fetchall()
        conn.close()
        return render_template("admin/orders.html", orders=orders_list)
    except Exception as e:
        return f"Database error: {e}"


@app.route("/admin/users")
def admin_users():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, email, role, created_at FROM users")
            users_list = cursor.fetchall()
        conn.close()
        return render_template("admin/users.html", users=users_list)
    except Exception as e:
        return f"Database error: {e}"


@app.route("/admin/sellers")
def admin_sellers():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT u.id, u.name, u.email, COUNT(b.id) as book_count
                FROM users u
                JOIN books b ON u.id = b.seller_id
                GROUP BY u.id
            """)
            sellers_list = cursor.fetchall()
        conn.close()
        return render_template("admin/sellers.html", sellers=sellers_list)
    except Exception as e:
        return f"Database error: {e}"


@app.route("/admin/reports")
def admin_reports():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Sales over time (grouped by date)
            cursor.execute("""
                SELECT DATE_FORMAT(created_at, '%Y-%m-%d') as sale_date, SUM(total_amount) as daily_revenue
                FROM orders
                GROUP BY sale_date
                ORDER BY sale_date ASC
            """)
            sales_rows = cursor.fetchall()
            
            # Popular categories (count of items sold)
            cursor.execute("""
                SELECT b.category_name, COUNT(oi.id) as sales_count
                FROM order_items oi
                JOIN books b ON oi.book_id = b.id
                GROUP BY b.category_name
                ORDER BY sales_count DESC
            """)
            category_rows = cursor.fetchall()
        conn.close()
        
        sales_dates = [row["sale_date"] for row in sales_rows]
        sales_revenues = [float(row["daily_revenue"]) for row in sales_rows]
        
        category_names = [row["category_name"] for row in category_rows]
        category_sales = [int(row["sales_count"]) for row in category_rows]
        
        return render_template(
            "admin/reports.html",
            sales_dates=sales_dates,
            sales_revenues=sales_revenues,
            category_names=category_names,
            category_sales=category_sales
        )
    except Exception as e:
        return f"Database error: {e}"


@app.route("/admin/export-report")
def admin_export_report():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.order_number, u.name as customer_name, o.total_amount, o.payment_method, o.status, o.created_at
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.id
                ORDER BY o.created_at DESC
            """)
            orders_list = cursor.fetchall()
        conn.close()
        
        import csv
        from io import StringIO
        from flask import make_response
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Order Number", "Customer Name", "Total Amount (INR)", "Payment Method", "Status", "Date Created"])
        for order in orders_list:
            cw.writerow([
                order["order_number"],
                order["customer_name"] or "Guest",
                order["total_amount"],
                order["payment_method"],
                order["status"],
                order["created_at"]
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=sales_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return f"Error exporting report: {e}"


@app.route("/admin/reports/income-statement")
def admin_export_income_statement():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE_FORMAT(created_at, '%Y-%m') as month, SUM(total_amount) as monthly_sales, COUNT(id) as total_orders
                FROM orders
                GROUP BY month
                ORDER BY month DESC
            """)
            statement_list = cursor.fetchall()
        conn.close()
        
        import csv
        from io import StringIO
        from flask import make_response
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Month", "Total Revenue (INR)", "Total Orders"])
        for row in statement_list:
            cw.writerow([row["month"], row["monthly_sales"], row["total_orders"]])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=income_statement.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return f"Error exporting income statement: {e}"


@app.route("/admin/reports/inventory-audit")
def admin_export_inventory_audit():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT b.id, b.title, b.author, b.category_name, b.price, b.book_condition, u.name as seller_name, b.approved, b.created_at
                FROM books b
                LEFT JOIN users u ON b.seller_id = u.id
                ORDER BY b.id DESC
            """)
            inventory_list = cursor.fetchall()
        conn.close()
        
        import csv
        from io import StringIO
        from flask import make_response
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Book ID", "Title", "Author", "Category", "Price (INR)", "Condition", "Seller", "Approved Status", "Date Listed"])
        for row in inventory_list:
            cw.writerow([
                row["id"],
                row["title"],
                row["author"],
                row["category_name"],
                row["price"],
                row["book_condition"],
                row["seller_name"] or "Store",
                "Approved" if row["approved"] else "Pending",
                row["created_at"]
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=inventory_audit.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return f"Error exporting inventory audit: {e}"


@app.route("/admin/reports/seller-verification")
def admin_export_seller_verification():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id, u.name, u.email, u.role, COUNT(b.id) as books_listed
                FROM users u
                LEFT JOIN books b ON u.id = b.seller_id
                WHERE u.role = 'User'
                GROUP BY u.id
                ORDER BY books_listed DESC
            """)
            seller_list = cursor.fetchall()
        conn.close()
        
        import csv
        from io import StringIO
        from flask import make_response
        
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Seller ID", "Seller Name", "Email", "Role", "Books Listed"])
        for row in seller_list:
            cw.writerow([
                row["id"],
                row["name"],
                row["email"],
                row["role"],
                row["books_listed"]
            ])
            
        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=seller_verification.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return f"Error exporting seller verification: {e}"


@app.route("/admin/settings")
def admin_settings():
    if "user" not in session or session.get("user") != "Admin":
        return redirect(url_for("admin_login"))
    return render_template("admin/settings.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ==========================
# API ENDPOINTS (MySQL Integration)
# ==========================

@app.route("/api/sync_data")
def api_sync_data():
    try:
        conn = get_db_connection()
        catalog = []
        cart = []
        wishlist = []
        
        with conn.cursor() as cursor:
            # 1. Fetch Catalog
            cursor.execute("""
                SELECT b.*, u.name AS seller_name 
                FROM books b 
                LEFT JOIN users u ON b.seller_id = u.id
            """)
            books_rows = cursor.fetchall()
            for row in books_rows:
                catalog.append({
                    "id": row["id"],
                    "title": row["title"],
                    "author": row["author"],
                    "price": float(row["price"]),
                    "original_price": float(row["original_price"]) if row["original_price"] is not None else None,
                    "img": row["img"],
                    "condition": row["book_condition"],
                    "description": row["condition_description"] or "",
                    "approved": bool(row["approved"]),
                    "category": row["category_name"],
                    "seller_name": row["seller_name"] or "Store"
                })
            
            # 2. Fetch User Cart and Wishlist if logged in
            if "user_id" in session:
                user_id = session["user_id"]
                
                # Cart
                cursor.execute("""
                    SELECT c.quantity, b.*
                    FROM cart_items c
                    JOIN books b ON c.book_id = b.id
                    WHERE c.user_id = %s
                """, (user_id,))
                cart_rows = cursor.fetchall()
                for row in cart_rows:
                    cart.append({
                        "id": row["id"],
                        "title": row["title"],
                        "author": row["author"],
                        "price": float(row["price"]),
                        "img": row["img"],
                        "quantity": row["quantity"]
                    })
                
                # Wishlist
                cursor.execute("""
                    SELECT b.*
                    FROM wishlist_items w
                    JOIN books b ON w.book_id = b.id
                    WHERE w.user_id = %s
                """, (user_id,))
                wish_rows = cursor.fetchall()
                for row in wish_rows:
                    wishlist.append({
                        "id": row["id"],
                        "title": row["title"],
                        "author": row["author"],
                        "price": float(row["price"]),
                        "img": row["img"]
                    })
                    
        conn.close()
        return jsonify({
            "catalog": catalog,
            "cart": cart,
            "wishlist": wishlist,
            "isLoggedIn": True if "user_id" in session else False
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cart/add", methods=["POST"])
def api_cart_add():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
    
    data = request.json
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id = %s AND book_id = %s", (session["user_id"], book_id))
            item = cursor.fetchone()
            if item:
                cursor.execute("UPDATE cart_items SET quantity = quantity + 1 WHERE id = %s", (item["id"],))
            else:
                cursor.execute("INSERT INTO cart_items (user_id, book_id, quantity) VALUES (%s, %s, 1)", (session["user_id"], book_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
        
    data = request.json
    book_id = data.get("book_id")
    delta = data.get("delta", 1)
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, quantity FROM cart_items WHERE user_id = %s AND book_id = %s", (session["user_id"], book_id))
            item = cursor.fetchone()
            if item:
                new_qty = item["quantity"] + delta
                if new_qty <= 0:
                    cursor.execute("DELETE FROM cart_items WHERE id = %s", (item["id"],))
                else:
                    cursor.execute("UPDATE cart_items SET quantity = %s WHERE id = %s", (new_qty, item["id"]))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
        
    data = request.json
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM cart_items WHERE user_id = %s AND book_id = %s", (session["user_id"], book_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wishlist/add", methods=["POST"])
def api_wishlist_add():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
        
    data = request.json
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("INSERT IGNORE INTO wishlist_items (user_id, book_id) VALUES (%s, %s)", (session["user_id"], book_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/wishlist/remove", methods=["POST"])
def api_wishlist_remove():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
        
    data = request.json
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM wishlist_items WHERE user_id = %s AND book_id = %s", (session["user_id"], book_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/book/add", methods=["POST"])
def api_book_add():
    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401
        
    data = request.json
    title = data.get("title")
    author = data.get("author")
    category = data.get("category", "Fiction")
    price = data.get("price")
    img = data.get("img")
    condition = data.get("condition", "pre-loved")
    description = data.get("description", "")
    
    if not (title and author and price):
        return jsonify({"error": "Missing required fields"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO books 
                (title, author, category_name, price, img, book_condition, condition_description, seller_id, approved) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)""",
                (title, author, category, price, img, condition, description, session["user_id"])
            )
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/book/approve", methods=["POST"])
def api_admin_book_approve():
    if session.get("user") != "Admin":
        return jsonify({"error": "Admin required"}), 403
        
    data = request.json
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("UPDATE books SET approved = TRUE WHERE id = %s", (book_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/admin/book/delete", methods=["POST"])
def api_admin_book_delete():
    if session.get("user") != "Admin":
        return jsonify({"error": "Admin required"}), 403
        
    data = request.json
    book_id = data.get("book_id")
    if not book_id:
        return jsonify({"error": "Book ID required"}), 400
        
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM books WHERE id = %s", (book_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==========================
# RUN (Checkout & Orders)
# ==========================

@app.route("/checkout")
def checkout():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/checkout.html")


@app.route("/orders")
def orders():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("user/orders.html")


@app.route("/place-order", methods=["POST"])
def place_order():
    if "user_id" not in session:
        return redirect(url_for("login"))
        
    payment = request.form.get("payment", "COD")
    payment_text = "Cash on Delivery"
    if payment == "UPI":
        payment_text = "UPI"
    elif payment == "CARD":
        payment_text = "Credit / Debit Card"
        
    import random
    order_number = f"#ORD-{random.randint(1000, 9999)}"
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get cart items
            cursor.execute("""
                SELECT c.quantity, b.id, b.price 
                FROM cart_items c
                JOIN books b ON c.book_id = b.id
                WHERE c.user_id = %s
            """, (session["user_id"],))
            cart_items = cursor.fetchall()
            
            if not cart_items:
                conn.close()
                return redirect(url_for("cart"))
                
            # Calculate total
            total_amount = sum(float(item["price"]) * item["quantity"] for item in cart_items)
            
            # Insert Order
            cursor.execute(
                """INSERT INTO orders (order_number, user_id, total_amount, payment_method, status) 
                VALUES (%s, %s, %s, %s, 'Processing')""",
                (order_number, session["user_id"], total_amount, payment_text)
            )
            order_id = cursor.lastrowid
            
            # Insert Order Items
            for item in cart_items:
                cursor.execute(
                    "INSERT INTO order_items (order_id, book_id, quantity, price) VALUES (%s, %s, %s, %s)",
                    (order_id, item["id"], item["quantity"], item["price"])
                )
                
            # Clear Cart
            cursor.execute("DELETE FROM cart_items WHERE user_id = %s", (session["user_id"],))
            
        conn.commit()
        conn.close()
        
        # Save last order details to session
        session["last_order_number"] = order_number
        session["last_order_payment"] = payment_text
        session["last_order_total"] = total_amount
        
        return redirect(url_for("orders"))
    except Exception as e:
        return f"Error placing order: {e}"


if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)