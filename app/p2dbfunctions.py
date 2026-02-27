import mysql.connector

def connect_to_db():
    return mysql.connector.connect (
    host = "localhost",
    user = "root",
    password = "your_password",
    database = "dummy_project")


def get_basic_info(cursor):

    queries = {
        "Total Suppliers": """
            SELECT COUNT(*) AS Total_Suppliers
            FROM suppliers;
        """,

        "Total Products": """
            SELECT COUNT(*) AS Total_Products
            FROM products;
        """,

        "Total Categories Dealing": """
            SELECT COUNT(DISTINCT category) AS Total_Categories
            FROM products;
        """,

        "Total sales value made in last eight months (quantity*price)": """
            SELECT ROUND(SUM(ABS(se.change_quantity)*p.price),2) AS total_sales_value_in_last_3_months
            FROM stock_entries AS se
            JOIN products AS p
            ON p.product_id=se.product_id
            WHERE se.change_type="Sale"
            AND se.entry_date >= (SELECT date_sub(max(entry_date), INTERVAL 8 MONTH) FROM stock_entries);
        """,

        "Total restock value made in last eight months": """
            SELECT round(SUM(ABS(se.change_quantity)*p.price),2) AS total_restock_values_in_last_8_months
            FROM stock_entries AS se
            JOIN products AS p
            ON p.product_id=se.product_id
            WHERE se.change_type="Restock"
            AND se.entry_date >= (SELECT date_sub(max(entry_date), INTERVAL 8 MONTH) FROM stock_entries);
        """,

        "below_reorder_no_pending": """
            SELECT COUNT(*) AS below_reorder_count
            FROM products AS P
            WHERE P.stock_quantity < P.reorder_level
              AND P.product_id NOT IN (
                  SELECT DISTINCT product_id
                  FROM reorders
                  WHERE status = 'Pending'
              );
        """
    }
    result = {}

    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()
        result[label] = list(row.values())[0]

    print(result)

    return result

def get_additional_tables(cursor):
        queries = {
            "Suppliers Contact Details": "SELECT supplier_name, contact_name, email, phone FROM suppliers;",
            "Product with their supplier and stock": """
                SELECT p.product_name,
                s.supplier_id,
                p.stock_quantity,
                p.reorder_level
                FROM products as P
                JOIN suppliers AS s ON
                p.supplier_id = s.supplier_id
                ORDER BY product_name ASC;
            """,
            "Products that need to be Reordered": """
                SELECT product_id, product_name, stock_quantity, reorder_level
                FROM products
                WHERE stock_quantity <= reorder_level;
            """
        }

        tables = {}

        for label, query in queries.items():
            cursor.execute(query)
            tables[label] = cursor.fetchall()

        return tables

def add_new_manual_id(cursor, db, p_name, p_category, p_price, p_stock, p_reorder, p_supplier):
    proc_call= "call AddNewProductManualID(%s, %s, %s, %s ,%s , %s)"
    params = (p_name, p_category, p_price, p_stock, p_reorder, p_supplier)
    cursor.execute(proc_call, params)
    db.comit()

def get_categories(cursor):
    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
    rows = cursor.fetchall()
    return [row["category"] for row in rows]

def get_suppliers(cursor):
    cursor.execute("SELECT supplier_id, supplier_name FROM suppliers ORDER BY supplier_name ASC")
    return cursor.fetchall()

def get_all_products(cursor):
    cursor.execute("SELECT product_id, product_name FROM products ORDER BY product_name")
    return cursor.fetchall()

def get_product_history(cursor, product_id):
    query = "SELECT * FROM product_inventory_history WHERE product_id = %s ORDER BY record_date DESC"
    cursor.execute(query, (product_id,))
    return cursor.fetchall()

def place_reorder(cursor, db, product_id, reorder_quantity):
    query = """
        INSERT INTO reorders (product_id, reorder_quantity, status, reorder_date)
        VALUES (%s, %s, 'Pending', CURDATE())
    """
    cursor.execute(query, (product_id, reorder_quantity))
    db.commit()
def get_pending_reorders(cursor):
    cursor.execute("""
    SELECT r.reorder_id, p.product_name 
    FROM reorders AS r JOIN products AS p 
    ON r.product_id = p.product_id
    """)
    return cursor.fetchall()

def mark_reorder_as_received(cursor, db, reorder_id):
    cursor.callproc("MarkReorderAsReceived", [reorder_id])
    db.commit()






















