import streamlit as st
import pandas as pd
import json
import os
import hashlib
from datetime import datetime, date
from io import BytesIO
import base64

# ============== SECURITY CONFIG ==============
# Simple PIN-based auth for client access
# Change this PIN before deploying! Use a strong password.
# Try Streamlit Cloud secrets first, fallback to hardcoded PIN for local dev
try:
    APP_PIN = st.secrets["app_pin"]
except (KeyError, FileNotFoundError):
    APP_PIN = "03218625988"  # Fallback PIN for local testing

# Session timeout (in seconds)
SESSION_TIMEOUT = 3600  # 1 hour

# ============== CONFIG ==============
st.set_page_config(
    page_title="Gujranwala Cheese & Food - Inventory",
    page_icon="🧀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== THEME ==============
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 800; color: #E65100; text-align: center; }
    .sub-header { font-size: 1.2rem; color: #555; text-align: center; margin-bottom: 20px; }
    .category-header { background: linear-gradient(90deg, #E65100, #FF9800); color: white; padding: 10px; border-radius: 8px; font-weight: 700; font-size: 1.1rem; margin-top: 15px; }
    .metric-card { background: #fff3e0; border-left: 4px solid #E65100; padding: 15px; border-radius: 8px; }
    .low-stock { background: #ffebee; border-left: 4px solid #c62828; }
    .out-stock { background: #fce4ec; border-left: 4px solid #880e4f; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background: #fff3e0; border-radius: 8px 8px 0 0; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background: #E65100 !important; color: white !important; }
    div[data-testid="stDataFrame"] td { font-size: 14px; }
    .sidebar-info { font-size: 0.85rem; color: #666; padding: 10px; background: #f5f5f5; border-radius: 8px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ============== DATA ==============
@st.cache_data
def get_default_inventory():
    return [
        {"id": 1, "name": "Pizza Cheese 70/30 Shredded", "category": "Pizza Cheese", "price_0_5kg": 800, "price_1kg": 1500, "price_2kg": 2800, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 2, "name": "Mozzarella 100%", "category": "Pizza Cheese", "price_0_5kg": 850, "price_1kg": 1600, "price_2kg": 3000, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 3, "name": "Cheese Slice Yellow", "category": "Burger Cheese", "price_0_5kg": 750, "price_1kg": 1400, "price_2kg": 2750, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 4, "name": "Cheese Slice White", "category": "Burger Cheese", "price_0_5kg": 750, "price_1kg": 1400, "price_2kg": 2750, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 5, "name": "Crispy Nuggets", "category": "Frozen Panchi", "price_0_5kg": 600, "price_1kg": 1100, "price_2kg": 2150, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 6, "name": "Crispy Jumbo Patty", "category": "Frozen Panchi", "price_0_5kg": 600, "price_1kg": 1100, "price_2kg": 2150, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 7, "name": "Crispy Regular Patty", "category": "Frozen Panchi", "price_0_5kg": 600, "price_1kg": 1100, "price_2kg": 2150, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 8, "name": "Chicken Gola Kabab", "category": "Frozen Panchi", "price_0_5kg": 600, "price_1kg": 1100, "price_2kg": 2150, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 9, "name": "Chicken Seekh Kabab", "category": "Frozen Panchi", "price_0_5kg": 700, "price_1kg": 1300, "price_2kg": 2500, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 10, "name": "Crispy Fries", "category": "Frozen Panchi", "price_0_5kg": 400, "price_1kg": 700, "price_2kg": 1500, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 11, "name": "Fajita Topping", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": 1350, "price_2kg": 2600, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 12, "name": "Creamy Topping", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": 1450, "price_2kg": 2800, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 13, "name": "Hot Wings Marinated", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": None, "price_2kg": 2000, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 14, "name": "Zinger Marinated", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": None, "price_2kg": 2400, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 15, "name": "Chicken Seekh Kabab (Small)", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": 500, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 16, "name": "Chicken Kofta", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": 350, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 17, "name": "Chicken Kofta (Large)", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": 500, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 18, "name": "Hot Short", "category": "Frozen Panchi", "price_0_5kg": None, "price_1kg": 600, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 19, "name": "Zesty Fillet", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1700, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 20, "name": "Chicken Poppers", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1350, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 21, "name": "Chicken Strips", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1350, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 22, "name": "Baked Wings", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1350, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 23, "name": "Chicron Fries", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1200, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 24, "name": "Crispy Nuggets (Sabroso)", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1200, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 25, "name": "Chicken Chapli", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1050, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 26, "name": "Jumbo Crispy Patty", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1250, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 27, "name": "Arabian Injected Patty", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1350, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 28, "name": "Arabian Injected Nuggets", "category": "Sabroso Frozen", "price_0_5kg": None, "price_1kg": 1350, "price_2kg": None, "unit": "kg", "stock": 0, "min_stock": 3, "status": "In Stock"},
        {"id": 29, "name": "Khadam's Desi Ghee 500gm", "category": "Desi Ghee", "price_0_5kg": 1350, "price_1kg": None, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 30, "name": "Khadam's Desi Ghee 1000gm", "category": "Desi Ghee", "price_0_5kg": None, "price_1kg": 2650, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 31, "name": "Khadam's Butter 250gm", "category": "Butter", "price_0_5kg": None, "price_1kg": 530, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 32, "name": "Khadam's Butter 500gm", "category": "Butter", "price_0_5kg": 1040, "price_1kg": None, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 33, "name": "Khadam's Butter 1000gm", "category": "Butter", "price_0_5kg": None, "price_1kg": 2060, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 34, "name": "Pizza Dough Floor 250gm", "category": "Pizza Dough", "price_0_5kg": None, "price_1kg": 500, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 35, "name": "Pizza Dough Floor 500gm", "category": "Pizza Dough", "price_0_5kg": 850, "price_1kg": None, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
        {"id": 36, "name": "Pizza Dough Floor 1000gm", "category": "Pizza Dough", "price_0_5kg": None, "price_1kg": 1600, "price_2kg": None, "unit": "pack", "stock": 0, "min_stock": 5, "status": "In Stock"},
    ]

# ============== SESSION STATE ==============
if "inventory" not in st.session_state:
    st.session_state.inventory = get_default_inventory()
if "transactions" not in st.session_state:
    st.session_state.transactions = []
if "sales" not in st.session_state:
    st.session_state.sales = []

# ============== AUTHENTICATION ==============
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.auth_time = None

# Check session timeout
if st.session_state.authenticated and st.session_state.auth_time:
    elapsed = (datetime.now() - st.session_state.auth_time).total_seconds()
    if elapsed > SESSION_TIMEOUT:
        st.session_state.authenticated = False
        st.session_state.auth_time = None
        st.warning("Session expired. Please login again.")
        st.rerun()

# Login screen
if not st.session_state.authenticated:
    st.markdown("<div class='main-header'>Gujranwala Cheese & Food</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Inventory Management System</div>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("https://img.icons8.com/color/96/cheese.png", width=100)
        st.markdown("### 🔐 Secure Login")
        pin_input = st.text_input("Enter PIN", type="password", placeholder="Enter your access PIN...")

        if st.button("Login", type="primary", use_container_width=True):
            if pin_input == APP_PIN:
                st.session_state.authenticated = True
                st.session_state.auth_time = datetime.now()
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid PIN. Access denied.")
                # Log failed attempt (optional)
                st.session_state.transactions.append({
                    "id": len(st.session_state.transactions) + 1,
                    "type": "Security",
                    "item": "Failed Login Attempt",
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "notes": f"IP: {st.query_params.get('client_ip', 'unknown')}"
                })

    st.stop()  # Block all other pages until authenticated

# ============== HELPERS ==============
def format_price(p):
    return f"Rs. {p:,}/-" if p else "N/A"

def get_status(stock, min_stock):
    if stock == 0:
        return "Out of Stock"
    elif stock <= min_stock:
        return "Low Stock"
    return "In Stock"

def get_status_color(status):
    return {"In Stock": "green", "Low Stock": "orange", "Out of Stock": "red"}.get(status, "gray")

def update_status():
    if "inventory" in st.session_state and st.session_state.inventory:
        for item in st.session_state.inventory:
            if isinstance(item, dict):
                item["status"] = get_status(item.get("stock", 0), item.get("min_stock", 5))

def save_to_json():
    data = {
        "inventory": st.session_state.inventory,
        "transactions": st.session_state.transactions,
        "sales": st.session_state.sales,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return json.dumps(data, indent=2, ensure_ascii=False)

def load_from_json(uploaded_file):
    data = json.load(uploaded_file)
    if not isinstance(data, dict):
        raise ValueError("Invalid backup format")
    st.session_state.inventory = data.get("inventory", []) or get_default_inventory()
    st.session_state.transactions = data.get("transactions", []) or []
    st.session_state.sales = data.get("sales", []) or []
    update_status()
    st.rerun()

def export_excel():
    try:
        import openpyxl
        df = pd.DataFrame(st.session_state.inventory)
        df["price_0_5kg"] = df["price_0_5kg"].apply(lambda x: format_price(x))
        df["price_1kg"] = df["price_1kg"].apply(lambda x: format_price(x))
        df["price_2kg"] = df["price_2kg"].apply(lambda x: format_price(x))
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Inventory", index=False)
            if st.session_state.transactions:
                try:
                    pd.DataFrame(st.session_state.transactions).to_excel(writer, sheet_name="Transactions", index=False)
                except Exception:
                    pass
            if st.session_state.sales:
                try:
                    pd.DataFrame(st.session_state.sales).to_excel(writer, sheet_name="Sales", index=False)
                except Exception:
                    pass
        output.seek(0)
        return output, "xlsx"
    except ImportError:
        df = pd.DataFrame(st.session_state.inventory)
        output = BytesIO()
        df.to_csv(output, index=False)
        output.seek(0)
        return output, "csv"
    except Exception as e:
        st.error(f"Export error: {e}")
        return None, "error"

# ============== SIDEBAR ==============
with st.sidebar:
    st.image("https://img.icons8.com/color/96/cheese.png", width=80)
    st.markdown("### Gujranwala Cheese & Food")
    st.markdown("**0321-8625988**")
    st.markdown("---")

    page = st.radio("Navigate", [
        "Dashboard",
        "Inventory",
        "Stock In",
        "Stock Out / Sales",
        "Transactions",
        "Sales Report",
        "Settings & Backup"
    ], index=0)

    st.markdown("---")
    st.markdown("<div class='sidebar-info'>Tip: Use 'Settings & Backup' to save your data as JSON. Upload that JSON to Google Drive for cloud backup.</div>", unsafe_allow_html=True)
    st.markdown("<div class='sidebar-info'>Data is stored in browser session. Export JSON regularly to avoid data loss.</div>", unsafe_allow_html=True)

# ============== DASHBOARD ==============
if page == "Dashboard":
    st.markdown("<div class='main-header'>Gujranwala Cheese & Food</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Inventory Management System | 0321-8625988</div>", unsafe_allow_html=True)

    update_status()
    df = pd.DataFrame(st.session_state.inventory)

    col1, col2, col3, col4, col5 = st.columns(5)
    total_items = len(df)
    in_stock = len(df[df["status"] == "In Stock"])
    low_stock = len(df[df["status"] == "Low Stock"])
    out_stock = len(df[df["status"] == "Out of Stock"])
    total_sales = sum(s.get("total", 0) for s in st.session_state.sales) if st.session_state.sales else 0

    col1.metric("Total Items", total_items)
    col2.metric("In Stock", in_stock, delta=f"{in_stock/total_items*100:.0f}%" if total_items > 0 else "0%")
    col3.metric("Low Stock", low_stock, delta=f"-{low_stock}" if low_stock > 0 else None, delta_color="inverse")
    col4.metric("Out of Stock", out_stock, delta=f"-{out_stock}" if out_stock > 0 else None, delta_color="inverse")
    col5.metric("Total Sales", f"Rs. {total_sales:,}")

    st.markdown("---")

    if low_stock > 0 or out_stock > 0:
        st.warning("Stock Alerts — Some items need attention!")
        alert_df = df[df["status"].isin(["Low Stock", "Out of Stock"])][["name", "category", "stock", "min_stock", "status"]]
        st.dataframe(alert_df, use_container_width=True, hide_index=True)
    else:
        st.success("All items are well stocked!")

    st.markdown("---")

    st.markdown("### Category Overview")
    cat_data = df.groupby("category").agg({"stock": "sum", "name": "count"}).rename(columns={"name": "items"}).reset_index()

    col_left, col_right = st.columns(2)
    with col_left:
        st.bar_chart(cat_data.set_index("category")["items"], use_container_width=True, color="#E65100")
    with col_right:
        st.bar_chart(cat_data.set_index("category")["stock"], use_container_width=True, color="#FF9800")

    st.markdown("### Recent Activity")
    if st.session_state.transactions:
        try:
            recent = pd.DataFrame(st.session_state.transactions[-10:])
            if not recent.empty:
                st.dataframe(recent, use_container_width=True, hide_index=True)
            else:
                st.info("No transactions yet. Start by adding stock!")
        except Exception:
            st.info("No transactions yet. Start by adding stock!")
    else:
        st.info("No transactions yet. Start by adding stock!")

# ============== INVENTORY ==============
elif page == "Inventory":
    st.markdown("<div class='main-header'>Full Inventory</div>", unsafe_allow_html=True)
    update_status()
    df = pd.DataFrame(st.session_state.inventory)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        search = st.text_input("Search items...", placeholder="Type item name...")
    with col_f2:
        cat_filter = st.multiselect("Category", df["category"].unique().tolist(), default=[])
    with col_f3:
        status_filter = st.multiselect("Status", ["In Stock", "Low Stock", "Out of Stock"], default=[])

    filtered = df.copy()
    if search:
        filtered = filtered[filtered["name"].str.contains(search, case=False, na=False)]
    if cat_filter:
        filtered = filtered[filtered["category"].isin(cat_filter)]
    if status_filter:
        filtered = filtered[filtered["status"].isin(status_filter)]

    display_cols = ["id", "name", "category", "price_0_5kg", "price_1kg", "price_2kg", "stock", "min_stock", "status"]
    display_df = filtered[display_cols].copy()
    display_df["price_0_5kg"] = display_df["price_0_5kg"].apply(format_price)
    display_df["price_1kg"] = display_df["price_1kg"].apply(format_price)
    display_df["price_2kg"] = display_df["price_2kg"].apply(format_price)

    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown(f"**Showing {len(filtered)} of {len(df)} items**")

# ============== STOCK IN ==============
elif page == "Stock In":
    st.markdown("<div class='main-header'>Add Stock (Purchase)</div>", unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.inventory)
    categories = df["category"].unique().tolist()

    selected_cat = st.selectbox("Select Category", categories)
    items_in_cat = df[df["category"] == selected_cat]["name"].tolist()
    selected_item = st.selectbox("Select Item", items_in_cat)

    item = next(i for i in st.session_state.inventory if i["name"] == selected_item)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Current Stock:** {item['stock']} {item['unit']}")
        st.markdown(f"**Min Stock:** {item['min_stock']} {item['unit']}")
        st.markdown(f"**Status:** :{get_status_color(item['status'])}[{item['status']}]")
    with col2:
        st.markdown(f"**0.5 KG:** {format_price(item['price_0_5kg'])}")
        st.markdown(f"**1 KG:** {format_price(item['price_1kg'])}")
        st.markdown(f"**2 KG:** {format_price(item['price_2kg'])}")

    st.markdown("---")

    col_qty, col_cost = st.columns(2)
    with col_qty:
        qty = st.number_input("Quantity to Add", min_value=1, value=1, step=1)
    with col_cost:
        cost = st.number_input("Cost per Unit (Rs.)", min_value=0, value=0, step=50)

    supplier = st.text_input("Supplier Name", placeholder="Enter supplier...")
    notes = st.text_area("Notes", placeholder="Any notes about this purchase...")

    if st.button("Add Stock", type="primary", use_container_width=True):
        item["stock"] += qty
        update_status()
        transaction = {
            "id": len(st.session_state.transactions) + 1,
            "type": "Stock In",
            "item": item["name"],
            "category": item["category"],
            "quantity": qty,
            "cost_per_unit": cost,
            "total_cost": cost * qty,
            "supplier": supplier,
            "notes": notes,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "new_stock": item["stock"]
        }
        st.session_state.transactions.append(transaction)
        st.success(f"Added {qty} {item['unit']} of {item['name']}. New stock: {item['stock']}")
        st.balloons()

# ============== STOCK OUT / SALES ==============
elif page == "Stock Out / Sales":
    st.markdown("<div class='main-header'>Sales / Stock Out</div>", unsafe_allow_html=True)

    df = pd.DataFrame(st.session_state.inventory)
    categories = df["category"].unique().tolist()

    selected_cat = st.selectbox("Select Category", categories)
    items_in_cat = df[df["category"] == selected_cat]["name"].tolist()
    selected_item = st.selectbox("Select Item", items_in_cat)

    item = next(i for i in st.session_state.inventory if i["name"] == selected_item)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Current Stock:** {item['stock']} {item['unit']}")
        st.markdown(f"**Min Stock:** {item['min_stock']} {item['unit']}")
        st.markdown(f"**Status:** :{get_status_color(item['status'])}[{item['status']}]")
    with col2:
        st.markdown(f"**0.5 KG:** {format_price(item['price_0_5kg'])}")
        st.markdown(f"**1 KG:** {format_price(item['price_1kg'])}")
        st.markdown(f"**2 KG:** {format_price(item['price_2kg'])}")

    st.markdown("---")

    size_options = []
    if item["price_0_5kg"]:
        size_options.append("0.5 KG")
    if item["price_1kg"]:
        size_options.append("1 KG")
    if item["price_2kg"]:
        size_options.append("2 KG")

    if not size_options:
        st.error("This item has no pricing configured!")
    elif item["stock"] <= 0:
        st.error("This item is OUT OF STOCK! Cannot make a sale.")
        st.warning("Go to 'Stock In' to add stock first.")
    else:
        col_size, col_qty = st.columns(2)
        with col_size:
            size = st.selectbox("Size", size_options)
        with col_qty:
            qty = st.number_input("Quantity Sold", min_value=1, max_value=max(1, item["stock"]), value=1, step=1)

        price_map = {"0.5 KG": item["price_0_5kg"], "1 KG": item["price_1kg"], "2 KG": item["price_2kg"]}
        unit_price = price_map[size]
        total = unit_price * qty

        st.markdown(f"**Unit Price:** {format_price(unit_price)}")
        st.markdown(f"**Total:** Rs. {total:,}/-")

        customer = st.text_input("Customer Name", placeholder="Enter customer name...")
        notes = st.text_area("Notes", placeholder="Any notes about this sale...")

        if st.button("Record Sale", type="primary", use_container_width=True):
            if qty > item["stock"]:
                st.error("Not enough stock!")
            else:
                item["stock"] -= qty
                update_status()

                transaction = {
                    "id": len(st.session_state.transactions) + 1,
                    "type": "Sale",
                    "item": item["name"],
                    "category": item["category"],
                    "size": size,
                    "quantity": qty,
                    "unit_price": unit_price,
                    "total": total,
                    "customer": customer,
                    "notes": notes,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "new_stock": item["stock"]
                }
                st.session_state.transactions.append(transaction)
                st.session_state.sales.append(transaction)
                st.success(f"Sale recorded! {qty}x {size} of {item['name']} = Rs. {total:,}/-")
                if item["stock"] <= item["min_stock"]:
                    st.warning(f"{item['name']} is now {item['status']}!")

# ============== TRANSACTIONS ==============
elif page == "Transactions":
    st.markdown("<div class='main-header'>All Transactions</div>", unsafe_allow_html=True)

    if not st.session_state.transactions:
        st.info("No transactions recorded yet.")
    else:
        trans_df = pd.DataFrame(st.session_state.transactions)

        col1, col2 = st.columns(2)
        with col1:
            type_filter = st.multiselect("Filter by Type", ["Stock In", "Sale"], default=["Stock In", "Sale"])
        with col2:
            if "date" in trans_df.columns and not trans_df.empty:
                try:
                    trans_df["date_only"] = pd.to_datetime(trans_df["date"], errors="coerce").dt.date
                    trans_df = trans_df.dropna(subset=["date_only"])
                    if not trans_df.empty:
                        min_d = trans_df["date_only"].min()
                        max_d = trans_df["date_only"].max()
                        date_range = st.date_input("Date Range", [min_d, max_d])
                    else:
                        date_range = []
                except Exception:
                    date_range = []
            else:
                date_range = []

        filtered_trans = trans_df[trans_df["type"].isin(type_filter)] if "type" in trans_df.columns else trans_df

        if filtered_trans.empty:
            st.info("No transactions match the selected filters.")
        else:
            st.dataframe(filtered_trans, use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("### Transaction Summary")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            stock_in_total = sum(t.get("total_cost", 0) for t in st.session_state.transactions if t.get("type") == "Stock In")
            st.metric("Total Purchases", f"Rs. {stock_in_total:,}")
        with col_b:
            sales_total = sum(t.get("total", 0) for t in st.session_state.transactions if t.get("type") == "Sale")
            st.metric("Total Sales", f"Rs. {sales_total:,}")
        with col_c:
            profit = sales_total - stock_in_total
            st.metric("Net Profit", f"Rs. {profit:,}", delta_color="normal" if profit >= 0 else "inverse")

# ============== SALES REPORT ==============
elif page == "Sales Report":
    st.markdown("<div class='main-header'>Sales Analytics</div>", unsafe_allow_html=True)

    if not st.session_state.sales:
        st.info("No sales data yet. Record some sales first!")
    else:
        sales_df = pd.DataFrame(st.session_state.sales)
        sales_df["date"] = pd.to_datetime(sales_df["date"], errors="coerce")
        sales_df = sales_df.dropna(subset=["date"])
        sales_df["date_only"] = sales_df["date"].dt.date

        min_date = sales_df["date_only"].min()
        max_date = sales_df["date_only"].max()

        try:
            date_range = st.date_input("Select Date Range", [min_date, max_date], key="sales_date")
        except Exception:
            date_range = [min_date, max_date]

        if len(date_range) == 2:
            mask = (sales_df["date_only"] >= date_range[0]) & (sales_df["date_only"] <= date_range[1])
            filtered_sales = sales_df[mask]
        else:
            filtered_sales = sales_df

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Orders", len(filtered_sales))
        with col2:
            st.metric("Revenue", f"Rs. {filtered_sales['total'].sum():,}")
        with col3:
            st.metric("Items Sold", filtered_sales['quantity'].sum())

        st.markdown("---")

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.markdown("### Sales by Category")
            cat_sales = filtered_sales.groupby("category")["total"].sum().reset_index()
            st.bar_chart(cat_sales.set_index("category"), use_container_width=True, color="#E65100")

        with col_chart2:
            st.markdown("### Top Selling Items")
            item_sales = filtered_sales.groupby("item")["quantity"].sum().sort_values(ascending=False).head(10)
            st.bar_chart(item_sales, use_container_width=True, color="#FF9800")

        st.markdown("### Daily Sales Trend")
        daily = filtered_sales.groupby("date_only")["total"].sum().reset_index()
        st.line_chart(daily.set_index("date_only"), use_container_width=True, color="#E65100")

        st.markdown("### Detailed Sales")
        st.dataframe(filtered_sales[["date", "item", "category", "size", "quantity", "unit_price", "total", "customer"]], use_container_width=True, hide_index=True)

# ============== SETTINGS & BACKUP ==============
elif page == "Settings & Backup":
    st.markdown("<div class='main-header'>Settings & Backup</div>", unsafe_allow_html=True)

    st.markdown("### Backup / Export Data")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Export as JSON (for Google Drive backup)**")
        json_data = save_to_json()
        st.download_button(
            label="Download JSON Backup",
            data=json_data,
            file_name=f"inventory_backup_{date.today()}.json",
            mime="application/json",
            use_container_width=True
        )
        st.info("Upload this JSON file to Google Drive for cloud backup!")

    with col2:
        st.markdown("**Export as Excel/CSV**")
        excel_result = export_excel()
        if excel_result is None or excel_result[1] == "error":
            st.error("Export failed. Please try again.")
        else:
            excel_data, ext = excel_result
            if ext == "xlsx":
                st.download_button(
                    label="Download Excel Report",
                    data=excel_data,
                    file_name=f"inventory_report_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("openpyxl not installed. Exporting as CSV instead.")
                st.download_button(
                    label="Download CSV Report",
                    data=excel_data,
                    file_name=f"inventory_report_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
                st.info("Install openpyxl: pip install openpyxl for Excel export")

    st.markdown("---")
    st.markdown("### Restore / Import Data")

    uploaded = st.file_uploader("Upload JSON Backup", type=["json"])
    if uploaded:
        if st.button("Restore Data", type="primary"):
            try:
                load_from_json(uploaded)
                st.success("Data restored successfully!")
            except json.JSONDecodeError:
                st.error("Invalid JSON file! Please upload a valid backup.")
            except Exception as e:
                st.error(f"Error restoring data: {str(e)}")

    st.markdown("---")
    st.markdown("### Reset Data")

    col_warn1, col_warn2 = st.columns(2)
    with col_warn1:
        confirm = st.checkbox("Confirm reset - ALL data will be lost!", key="confirm_reset")
        if confirm and st.button("Reset to Default Inventory", use_container_width=True):
            st.session_state.inventory = get_default_inventory()
            st.session_state.transactions = []
            st.session_state.sales = []
            st.success("Reset to default inventory!")
            st.rerun()
    with col_warn2:
        st.warning("This will erase all stock levels, transactions, and sales data!")

    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    **Gujranwala Cheese & Food Inventory System**
    - Built with Streamlit for easy deployment
    - All data stored in browser session (temporary)
    - Export JSON regularly for persistence
    - Upload JSON to Google Drive for cloud backup
    - Contact: **0321-8625988**
    """)

# Footer
st.markdown("---")
st.markdown("<div style='text-align:center; color:#999; font-size:0.85rem;'>Gujranwala Cheese & Food | Inventory System v1.0 | 0321-8625988</div>", unsafe_allow_html=True)
