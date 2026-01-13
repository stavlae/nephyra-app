# ==============================
# Néphyra - Streamlit App με Login & Μόνιμη Αποθήκευση
# ==============================

import os
import datetime
import hashlib
import pandas as pd

# ---- Safe imports για online IDE ----
try:
    import streamlit as st
except ModuleNotFoundError:
    print("Streamlit δεν είναι εγκατεστημένο. Αποθήκευσε τον κώδικα!")
    st = None

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    print("Matplotlib δεν είναι εγκατεστημένο!")
    plt = None

try:
    from PIL import Image
except ModuleNotFoundError:
    print("Pillow δεν είναι εγκατεστημένο!")
    Image = None

# ---- Φάκελοι και αρχεία ----
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.csv")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

if st is not None and plt is not None and Image is not None:

    # ---- Login / Registration ----
    st.title("Néphyra - Κοστολόγιο Κεριών (Login)")

    if 'login_status' not in st.session_state:
        st.session_state.login_status = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None

    # ---- Φόρτωση χρηστών ----
    if os.path.exists(USERS_FILE):
        users_df = pd.read_csv(USERS_FILE)
    else:
        users_df = pd.DataFrame(columns=['email','password'])

    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register(email, password):
        if email in users_df['email'].values:
            st.warning("Το email υπάρχει ήδη.")
            return False
        new_user = pd.DataFrame({'email':[email],'password':[hash_password(password)]})
        new_user.to_csv(USERS_FILE, mode='a', header=not os.path.exists(USERS_FILE), index=False)
        st.success("Ο λογαριασμός δημιουργήθηκε!")
        return True

    def login(email, password):
        hashed = hash_password(password)
        if email in users_df['email'].values:
            stored = users_df.loc[users_df['email']==email,'password'].values[0]
            if hashed == stored:
                st.session_state.login_status = True
                st.session_state.current_user = email
                return True
        st.error("Λάθος email ή password.")
        return False

    # ---- Forms ----
    login_tab, register_tab = st.tabs(["Login", "Register"])

    with login_tab:
        login_email = st.text_input("Email", key="login_email")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        if st.button("Σύνδεση"):
            if login(login_email, login_pass):
                st.experimental_rerun()

    with register_tab:
        reg_email = st.text_input("Email", key="reg_email")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        if st.button("Δημιουργία Λογαριασμού"):
            if register(reg_email, reg_pass):
                st.experimental_rerun()

    # ---- Αν ο χρήστης είναι συνδεδεμένος, ανοίγουμε το app ----
    if st.session_state.login_status:

        user = st.session_state.current_user
        st.header(f"Καλώς ήρθες, {user}")

        # ---- Paths για δεδομένα χρήστη ----
        user_dir = os.path.join(DATA_DIR, user.replace('@','_').replace('.','_'))
        if not os.path.exists(user_dir):
            os.makedirs(user_dir)
        MATERIALS_FILE = os.path.join(user_dir, "materials.csv")
        PRODUCTS_FILE = os.path.join(user_dir, "products.csv")
        ORDERS_FILE = os.path.join(user_dir, "orders.csv")

        # ---- Brand & Logo ----
        brand_name = st.text_input("Βάλε το brand name σου", "Néphyra")
        logo = st.file_uploader("Ανέβασε το λογότυπό σου", type=["png","jpg","jpeg"])
        if logo:
            img = Image.open(logo)
            st.image(img, width=200)

        # ---- Πρώτες Ύλες ----
        if 'materials' not in st.session_state:
            if os.path.exists(MATERIALS_FILE):
                st.session_state.materials = pd.read_csv(MATERIALS_FILE, index_col=0).to_dict()['cost']
            else:
                st.session_state.materials = {}

        st.subheader("Πρώτες Ύλες")
        mat_name = st.text_input("Όνομα πρώτης ύλης", key="mat_name")
        mat_cost = st.number_input("Κόστος ανά μονάδα", min_value=0.0, step=0.01, key="mat_cost")
        if st.button("Πρόσθεσε πρώτη ύλη"):
            if mat_name:
                st.session_state.materials[mat_name] = mat_cost
                pd.DataFrame.from_dict({'cost': st.session_state.materials}, orient='index').to_csv(MATERIALS_FILE)
        st.write("Τρέχουσες πρώτες ύλες:", st.session_state.materials)

        # ---- Προϊόντα / Συνταγές ----
        if 'products' not in st.session_state:
            if os.path.exists(PRODUCTS_FILE):
                df_prod = pd.read_csv(PRODUCTS_FILE)
                st.session_state.products = {row['product']: {k: v for k, v in row.items() if k not in ['product']} for _, row in df_prod.iterrows()}
            else:
                st.session_state.products = {}

        st.subheader("Προϊόντα / Συνταγές")
        prod_name = st.text_input("Όνομα προϊόντος", key="prod_name")
        prod_mat = st.selectbox("Επίλεξε πρώτη ύλη", list(st.session_state.materials.keys()) if st.session_state.materials else [""])
        prod_qty = st.number_input("Ποσότητα υλικού στο προϊόν", min_value=0.0, step=0.1, key="prod_qty")
        if st.button("Πρόσθεσε προϊόν"):
            if prod_name and prod_mat:
                if prod_name not in st.session_state.products:
                    st.session_state.products[prod_name] = {}
                st.session_state.products[prod_name][prod_mat] = prod_qty
                rows = []
                for p, mats in st.session_state.products.items():
                    row = {'product': p}
                    row.update(mats)
                    rows.append(row)
                pd.DataFrame(rows).to_csv(PRODUCTS_FILE, index=False)
        st.write("Τρέχοντα προϊόντα:", st.session_state.products)

        # ---- Παραγγελίες ----
        if 'order_history' not in st.session_state:
            if os.path.exists(ORDERS_FILE):
                st.session_state.order_history = pd.read_csv(ORDERS_FILE).to_dict('records')
            else:
                st.session_state.order_history = []

        st.subheader("Καταχώρηση Παραγγελίας")
        prod_order = st.selectbox("Επίλεξε προϊόν για παραγγελία", list(st.session_state.products.keys()) if st.session_state.products else [""])
        prod_qty_order = st.number_input("Ποσότητα προϊόντος", min_value=0, step=1, key="order_qty")
        order_date = st.date_input("Ημερομηνία παραγγελίας", datetime.date.today(), key="order_date")

        if st.button("Καταχώρηση παραγγελίας"):
            if prod_order:
                cost_per_product = sum([st.session_state.materials[m]*qty for m, qty in st.session_state.products[prod_order].items()])
                total_cost_order = cost_per_product * prod_qty_order
                st.session_state.order_history.append({
                    "Ημερομηνία": order_date,
                    "Προϊόν": prod_order,
                    "Ποσότητα": prod_qty_order,
                    "Κόστος ανά τεμάχιο": round(cost_per_product,2),
                    "Σύνολο": round(total_cost_order,2)
                })
                pd.DataFrame(st.session_state.order_history).to_csv(ORDERS_FILE, index=False)

        # ---- Ιστορικό Παραγγελιών / Γραφήματα ----
        st.subheader("Ημερολόγιο Κινήσεων Παραγγελιών")
        if st.session_state.order_history:
            df_history = pd.DataFrame(st.session_state.order_history)
            st.write(df_history)

            # Γράφημα κόστους ανά προϊόν
            st.subheader("Γράφημα Κόστους ανά Προϊόν")
            df_grouped_prod = df_history.groupby("Προϊόν")["Σύνολο"].sum().reset_index()
            fig1, ax1 = plt.subplots()
            ax1.bar(df_grouped_prod["Προϊόν"], df_grouped_prod["Σύνολο"], color='orange')
            ax1.set_ylabel("Σύνολο Κόστους (€)")
            ax1.set_xlabel("Προϊόν")
            ax1.set_title("Σύνολο Κόστους ανά Προϊόν")
            st.pyplot(fig1)

            # Γράφημα κόστους ανά ημερομηνία
            st.subheader("Γράφημα Κόστους ανά Ημερομηνία")
            df_grouped_date = df_history.groupby("Ημερομηνία")["Σύνολο"].sum().reset_index()
            fig2, ax2 = plt.subplots()
            ax2.plot(df_grouped_date["Ημερομηνία"], df_grouped_date["Σύνολο"], marker='o', linestyle='-')
            ax2.set_ylabel("Σύνολο Κόστους (€)")
            ax2.set_xlabel("Ημερομηνία")
            ax2.set_title("Κόστος Παραγγελιών ανά Ημερομηνία")
            plt.xticks(rotation=45)
            st.pyplot(fig2)

            # Download CSV
            csv = df_history.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Κατέβασε το ιστορικό παραγγελιών (CSV)",
                data=csv,
                file_name=f'kostologio_{brand_name}.csv',
                mime='text/csv'
            )