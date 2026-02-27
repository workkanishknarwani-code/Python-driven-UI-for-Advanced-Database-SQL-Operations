CREATE DATABASE dummy_project;
USE dummy_project;
SELECT*FROM products;
SELECT*FROM reorders;
SELECT*FROM shipments;
SELECT*FROM stock_entries;
SELECT*FROM suppliers;

/*
These 5 coloumns are connected wih each other in the following way:
supplier is connected with products and shipment through supplier_id; products is connected to reorder shipment and stock_entries through
product_id.
*/

-- 1. Total Suppliers
SELECT COUNT(*) as Total_Suppliers FROM suppliers;

-- 2. Total Products
SELECT COUNT(*) as Total_Products FROM products;

-- 3. Total Categories Dealing
SELECT COUNT(DISTINCT category) as Total_Categories FROM products; 

-- 4. Total sales value made in last eight months (quantity*price)
SELECT ROUND(SUM(ABS(se.change_quantity)*p.price),2) AS total_sales_value_in_last_3_months
FROM stock_entries AS se
JOIN products AS p
ON p.product_id=se.product_id
WHERE se.change_type="Sale"
AND se.entry_date>=
	(SELECT date_sub(max(entry_date), INTERVAL 8 MONTH) FROM stock_entries
);

-- 5. Total restock value made in last eight months
SELECT round(SUM(ABS(se.change_quantity)*p.price),2) AS total_restock_values_in_last_8_months
FROM stock_entries AS se
JOIN products AS p
ON p.product_id=se.product_id
WHERE se.change_type="Restock"
AND se.entry_date>=
	(SELECT date_sub(max(entry_date), INTERVAL 8 MONTH) FROM stock_entries
);

-- 6. Below Reorder and no Pending Reorders
SELECT COUNT(*) AS below_reorder_count
FROM products AS P
WHERE P.stock_quantity < P.reorder_level
AND P.product_id NOT IN (
    SELECT DISTINCT product_id
    FROM reorders
    WHERE status = 'Pending'
);

 -- 7. Suppliers and Their Contact Details  
SELECT supplier_name, contact_name, email, phone FROM suppliers;
 
 -- 8. Product with their Suppliers and Current Stock
SELECT p.product_name, s.supplier_id, p.stock_quantity, p.reorder_level 
FROM products as P
JOIN suppliers AS s ON 
p.supplier_id=s.supplier_id
ORDER BY product_name ASC;
 
-- 9. Products that need to be Reordered
SELECT product_id, product_name, stock_quantity, reorder_level FROM products WHERE stock_quantity<reorder_level;

-- 10. Add a new product to the database
DELIMITER $$
CREATE PROCEDURE AddNewProductManualID(
    IN p_name VARCHAR(225),
    IN p_category VARCHAR(100),
    IN p_price DECIMAL(10,2),
    IN p_stock INT,
    IN p_reorder INT,
    IN p_supplier INT
)
BEGIN
	DECLARE new_prod_id int;
    DECLARE new_shipment_id int;
	DECLARE new_entry_id int; 
    
    #make changes in product id 
	#generate the product id 
    SELECT MAX(product_id)+1 INTO new_prod_id FROM products;
    
    INSERT INTO products(product_id, product_name, category, price, stock_quantity, reorder_level, supplier_id)
    VALUES (new_prod_id, p_name, p_category, p_price, p_stock, p_reorder, p_supplier);
    
    #make changes in shipment table 
    #generate the shipment id 
    SELECT MAX(shipment_id)+1 INTO new_shipment_id FROM shipments;
    INSERT INTO shipments(shipment_id, product_id, supplier_id, quantity_received, shipment_date)
    VALUES (new_shipment_id, new_prod_id, p_supplier, p_stock, curdate());
    
    #make changes in stock_entries 
    #generate stock entries
    SELECT MAX(entry_id)+1 INTO new_entry_id FROM stock_entries;
    INSERT INTO  stock_entries(entry_id, product_id, change_quantity, change_type, entry_date)
    VALUES (new_entry_id, new_prod_id, p_stock, "Retock", curdate());
end $$
DELIMITER ;

#CALL AddNewProductManualID('Smart Watch', 'Electronics', 99.99, 100, 25, 5)

-- 11. Product History; finding shipment, sales, and purchase
CREATE OR REPLACE VIEW product_inventory_history AS
SELECT pih.product_id, pih.record_type, pih.record_date, pih.quantity, pih.change_type, pr.supplier_id FROM (
SELECT product_id, 
	"Shipment" AS record_type, 
    shipment_date AS record_date, 
    quantity_received AS quantity,
	null change_type
FROM shipments

UNION ALL 

SELECT product_id,
	"Stock Entry" AS record_type,
    entry_date AS record_date,
    change_quantity AS quantity,
    change_type
FROM stock_entries) AS pih 
JOIN products AS pr ON pr.product_id=pih.product_id;

#Now we don't have to write this comlete code (after using view) to check our product history. We can just write the code given below.

/*
SELECT * FROM product_inventoty_history 
WHERE product_id = 123
ORDER BY record_date DESC 
*/ 

-- 12. Place a re-order
INSERT INTO reorders(reorder_id, product_id, reorder_quantity, reorder_date, status)
SELECT MAX(reorder_id)+1, 101, 200, curdate(), "ordered" FROM reorders;

-- 13. Receiving reorders
/* When we receive a order it would effect 3 to 4 rows. So we will code using transaction ( it is a command in Sequel which works either together 
or doesn't work at all.*/
Delimiter $$
CREATE PROCEDURE MarkReorderAsReceived( in in_reorder_id INT)
BEGIN
DECLARE prod_id INT;
DECLARE qty INT; 
DECLARE sup_id INT;
DECLARE new_shipment_id INT;
DECLARE new_entry_id INT;

START TRANSACTION;
-- get product_id, quantity from reorders
SELECT product_id, reorder_quantity
INTO prod_id, qty
FROM reorders
WHERE reorder_id = in_reorder_id;

-- get supplier_id from product
SELECT supplier_id
INTO sup_id
FROM products
WHERE product_id = prod_id;

-- Update reorder table -- received
UPDATE reorders
SET STATUS = "Received"
WHERE reorder_id = in_reorder_id;

-- Update quantity in product table
UPDATE products
SET stock_quantity = stock_quantity+qty
WHERE product_id = prod_id;

-- Insert record into shipmen table
SELECT MAX(shipment_id)+1 INTO new_shipment_id FROM shipments;
INSERT INTO shipments(shipment_id, product_id, supplier_id, quantity_received, shipment_date)
VALUES (new_shipment_id, prod_id, sup_id, qty, CURDATE());

-- Insert record into Restock
SELECT MAX(entry_id)+1 INTO new_entry_id FROM stock_entries;
INSERT INTO stock_entries(entry_id, product_id, change_quantity, change_type, entry_date)
VALUES(new_entry_id, prod_id, qty, "Restock", CURDATE());

COMMIT;

END$$
DELIMITER ;
	
