from sys import exception

import streamlit as st
import pandas as pd
from p2dbfunctions import (
    connect_to_db,
    get_basic_info,
    get_additional_tables,
    get_categories,
    get_suppliers,
    get_all_products,
    get_product_history,
    place_reorder,
    mark_reorder_as_received,
    get_pending_reorders
)

from p2dbfunctions import(add_new_manual_id)

#For making sidebar
st.sidebar.title("Inventory Management Dashboard")
options = st.sidebar.radio("Select Option:", ["Basic Information", "Operational Tasks"])

#For creating main Space
st.title ("Inventory and Supply Chain Dashboard")
db=connect_to_db()
cursor=db.cursor(dictionary=True)

#---------- Basic Information Page ----------

if options=="Basic Information":
    st.header("Basic Metrics")

    #Getting basic information from database
    basic_info = get_basic_info(cursor)

    #If we want to divide our working area into rows and columns we have a function "cols"
    cols = st.columns(3)
    keys = list(basic_info.keys())

    for i in range(3):
        cols[i].metric(label=keys[i], value=basic_info[keys[i]])

    cols = st.columns(3)
    for i in range(3,6):
        cols[i-3].metric(label=keys[i], value=basic_info[keys[i]])

    st.divider()

    #Fetching and Displaying Detailed Tables
    tables = get_additional_tables(cursor)
    for labels, data in tables.items():
        st.header(labels)
        df = pd.DataFrame(data)
        st.dataframe(df)
        st.divider()

elif options == "Operational Tasks":
    st.header("Operational Tasks")

    Selected_Task = st.selectbox(
        "Choose a Task",
        ["Add New Product", "Product History", "Place Reorder", "Receive Reorder"]
    )

    if Selected_Task == "Add New Product":
        st.header("Add New Product")

        categories = get_categories(cursor)
        suppliers = get_suppliers(cursor)

        with st.form("Add_Product_Form"):
            product_name = st.text_input("Product_Name")
            product_category = st.selectbox("Category", categories)
            product_price = st.number_input("Price", min_value=0.00)
            product_stock = st.number_input("Stock Quantity", min_value=0, step=1)
            product_level = st.number_input("Reorder Level", min_value=0, step=1)
            supplier_ids = [s["supplier_id"] for s in suppliers]
            supplier_names = [s["supplier_name"] for s in suppliers]

            supplier_id = st.selectbox(
                "supplier",
                options=supplier_ids,
                format_func=lambda x: supplier_names[supplier_ids.index(x)]
            )

            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("Please enter product name")
                else:
                    try:
                        add_new_manual_id(
                            cursor,
                            db,
                            product_name,
                            product_category,
                            product_price,
                            product_stock,
                            product_level,
                            supplier_id
                        )
                        st.success(f"Product '{product_name}' added successfully")
                    except Exception as e:
                        st.error(f"Error adding the product: {e}")

    # ---------- Product History ----------

    if Selected_Task == "Product History":
        st.header("Product Inventory History")

        #Getting products' list
        products = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        selected_product_name = st.selectbox("Select a product", options=product_names)

        if selected_product_name:
            selected_product_id = product_ids[product_names.index(selected_product_name)]
            history_data = get_product_history(cursor, selected_product_id)

            if history_data:
                df = pd.DataFrame(history_data)
                st.dataframe(df)

            else:
                st.info("No history found for the product selected")

#---------- Place Reorder ----------

    if Selected_Task == "Place Reorder":
        st.header("Place a reorder")
        products = get_all_products(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        selected_product_name = st.selectbox("Select a product", options=product_names)
        reorder_qty = st.number_input("Reorder Quantity", min_value=1, step=1)

        if st.button("Place Reorder"):
            if not selected_product_name:
                st.error("Please select a product")
            elif reorder_qty < 0:
                st.error("Reorder quantity must be greater than zero")
            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]
                try:
                    place_reorder(cursor, db, selected_product_id, reorder_qty)
                    st.success(f"Order placed for {selected_product_name} with quantity {reorder_qty}")
                except Exception as e:
                    st.error(f"Error placing reorder: {e}")

#---------- Receiving a reorder ----------

    elif Selected_Task == "Receive Reorder":
        st.header("Mark reorder as received")
        #Fetch orders in ordered stage
        pending_reorders = get_pending_reorders(cursor)
        if not pending_reorders:
            st.info("No pending reorders found")
        else:
            reorder_ids = [r['reorder_id'] for r in pending_reorders]
            reorder_labels = [f"ID {r['reorder_id']} -str {r['product_name']}" for r in pending_reorders]

            selected_label = st.selectbox("Select reorder to mark as received", options=reorder_labels)
            if selected_label:
                selected_reorder_id = reorder_ids[reorder_labels.index(selected_label)]

                if st.button("Mark as received"):
                    try:
                        mark_reorder_as_received(cursor, db, selected_reorder_id)
                        st.success(f"Reorder ID {selected_reorder_id} marked as received")
                    except Exception as e:
                        st.error(f"Error {e}")