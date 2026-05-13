import streamlit as st
import os
import datetime
import smtplib
from email.message import EmailMessage
import re
import pandas as pd
import hashlib

# -----------------------------
# CONFIGURATION
# -----------------------------
DONORS_FILE = "donors.txt"
HOSPITALS_FILE = "hospitals.txt"

# Replace with your credentials
EMAIL_ADDRESS = "your_email@gmail.com"
EMAIL_PASSWORD = "your_app_password"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Pakistan Cities
PAKISTAN_CITIES = [
    "Islamabad", "Karachi", "Lahore", "Rawalpindi", "Faisalabad",
    "Multan", "Peshawar", "Quetta", "Sialkot", "Gujranwala",
    "Hyderabad", "Abbottabad", "Bahawalpur", "Sargodha", "Sukkur",
    "Larkana", "Sheikhupura", "Rahim Yar Khan", "Jhang", "Dera Ghazi Khan",
    "Gujrat", "Sahiwal", "Wah Cantonment", "Mardan", "Kasur",
    "Mingora", "Nawabshah", "Okara", "Gilgit", "Chiniot"
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# -----------------------------
# FILE OPERATIONS - DONORS
# -----------------------------
def initialize_files():
    if not os.path.exists(DONORS_FILE):
        with open(DONORS_FILE, "w") as f:
            pass

    if not os.path.exists(HOSPITALS_FILE):
        with open(HOSPITALS_FILE, "w") as f:
            pass


def read_donors():
    donors = []

    if not os.path.exists(DONORS_FILE):
        return donors

    with open(DONORS_FILE, "r") as file:
        for line in file:
            try:
                name, blood, loc, phone, email, cnic, last = line.strip().split("|")

                donors.append({
                    "name": name,
                    "blood": blood,
                    "location": loc,
                    "phone": phone,
                    "email": email,
                    "cnic": cnic,
                    "last": last
                })

            except ValueError:
                continue

    return donors


def write_donors(donors):
    with open(DONORS_FILE, "w") as file:
        for d in donors:
            file.write(
                f"{d['name']}|{d['blood']}|{d['location']}|{d['phone']}|{d['email']}|{d['cnic']}|{d['last']}\n"
            )


# -----------------------------
# FILE OPERATIONS - HOSPITALS
# -----------------------------
def read_hospitals():
    hospitals = []

    if not os.path.exists(HOSPITALS_FILE):
        return hospitals

    with open(HOSPITALS_FILE, "r") as file:
        for line in file:
            try:
                name, username, password_hash, phone = line.strip().split("|")

                hospitals.append({
                    "name": name,
                    "username": username,
                    "password_hash": password_hash,
                    "phone": phone
                })

            except ValueError:
                continue

    return hospitals


def write_hospitals(hospitals):
    with open(HOSPITALS_FILE, "w") as file:
        for h in hospitals:
            file.write(
                f"{h['name']}|{h['username']}|{h['password_hash']}|{h['phone']}\n"
            )


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def verify_login(username, password):

    # Admin Login
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        return "admin", "Admin"

    # Hospital Login
    hospitals = read_hospitals()
    password_hash = hash_password(password)

    for h in hospitals:
        if h["username"] == username and h["password_hash"] == password_hash:
            return "hospital", h["name"]

    return None, None


# -----------------------------
# VALIDATION FUNCTIONS
# -----------------------------
def is_eligible(last_donation):

    if last_donation == "None":
        return True

    last_date = datetime.datetime.strptime(last_donation, "%Y-%m-%d").date()
    today = datetime.date.today()

    return (today - last_date).days >= 90


def validate_phone(phone):
    pattern = r"^03\d{9}$"
    return re.match(pattern, phone) is not None


def validate_email(email):
    pattern = r"^[a-zA-Z0-9._%+-]+@gmail\.com$"
    return re.match(pattern, email) is not None


def validate_name(name):
    return len(name.strip()) >= 3 and name.replace(" ", "").isalpha()


def validate_cnic(cnic):
    pattern = r"^\d{13}$"
    return re.match(pattern, cnic) is not None


# -----------------------------
# EMAIL FUNCTION
# -----------------------------
def send_email(receiver, subject, body):

    try:
        msg = EmailMessage()

        msg["From"] = EMAIL_ADDRESS
        msg["To"] = receiver
        msg["Subject"] = subject

        msg.set_content(body)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)

        return True

    except Exception as e:
        st.error(f"Email error: {e}")
        return False


# -----------------------------
# ADMIN DASHBOARD
# -----------------------------
def admin_dashboard():

    st.markdown(
        '<h1 class="main-header">👨‍💼 Admin Dashboard</h1>',
        unsafe_allow_html=True
    )

    menu = st.sidebar.selectbox(
        "📋 Admin Menu",
        [
            "🏠 Home",
            "🏥 Register Hospital",
            "👥 View Hospitals",
            "🗑️ Delete Hospital"
        ]
    )

    # -----------------------------
    # HOME
    # -----------------------------
    if menu == "🏠 Home":

        hospitals = read_hospitals()
        donors = read_donors()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Hospitals", len(hospitals))

        with col2:
            st.metric("Total Donors", len(donors))

        with col3:
            eligible_donors = sum(
                1 for d in donors if is_eligible(d["last"])
            )

            st.metric("Eligible Donors", eligible_donors)

        st.markdown("---")

        st.info(
            "Manage hospitals and monitor the blood donation network."
        )

    # -----------------------------
    # REGISTER HOSPITAL
    # -----------------------------
    elif menu == "🏥 Register Hospital":

        st.subheader("Register New Hospital")

        with st.form("register_hospital_form"):

            col1, col2 = st.columns(2)

            with col1:
                hosp_name = st.text_input("Hospital Name")
                hosp_username = st.text_input("Username")

            with col2:
                hosp_password = st.text_input(
                    "Password",
                    type="password"
                )

                hosp_phone = st.text_input("Phone Number")

            submitted = st.form_submit_button("Register Hospital")

            if submitted:

                if not all([
                    hosp_name,
                    hosp_username,
                    hosp_password,
                    hosp_phone
                ]):
                    st.error("All fields are required!")

                elif not validate_phone(hosp_phone):
                    st.error("Invalid phone number!")

                else:

                    hospitals = read_hospitals()

                    if any(
                        h["username"] == hosp_username
                        for h in hospitals
                    ):
                        st.error("Username already exists!")

                    else:

                        hospitals.append({
                            "name": hosp_name,
                            "username": hosp_username,
                            "password_hash": hash_password(hosp_password),
                            "phone": hosp_phone
                        })

                        write_hospitals(hospitals)

                        st.success("Hospital registered successfully!")

    # -----------------------------
    # VIEW HOSPITALS
    # -----------------------------
    elif menu == "👥 View Hospitals":

        st.subheader("Registered Hospitals")

        hospitals = read_hospitals()

        if hospitals:

            df = pd.DataFrame(hospitals)
            df = df.drop(columns=["password_hash"])

            st.dataframe(df, use_container_width=True)

        else:
            st.info("No hospitals registered yet.")

    # -----------------------------
    # DELETE HOSPITAL
    # -----------------------------
    elif menu == "🗑️ Delete Hospital":

        st.subheader("Delete Hospital")

        hospitals = read_hospitals()

        if not hospitals:
            st.warning("No hospitals available.")

        else:

            usernames = [h["username"] for h in hospitals]

            selected = st.selectbox(
                "Select Hospital",
                usernames
            )

            if st.button("Delete Hospital"):

                hospitals = [
                    h for h in hospitals
                    if h["username"] != selected
                ]

                write_hospitals(hospitals)

                st.success("Hospital deleted successfully!")
                st.rerun()


# -----------------------------
# HOSPITAL DASHBOARD
# -----------------------------
def hospital_dashboard(hospital_name):

    st.markdown(
        f'<h1 class="main-header">🏥 {hospital_name}</h1>',
        unsafe_allow_html=True
    )

    menu = st.sidebar.selectbox(
        "📋 Hospital Menu",
        [
            "🏠 Home",
            "➕ Add Donor",
            "🩸 Donate Blood",
            "🚨 Request Blood",
            "👥 View Donors",
            "🗑️ Delete Donor"
        ]
    )

    # -----------------------------
    # HOME
    # -----------------------------
    if menu == "🏠 Home":

        donors = read_donors()

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Donors", len(donors))

        with col2:
            eligible = sum(
                1 for d in donors if is_eligible(d["last"])
            )

            st.metric("Eligible Donors", eligible)

        with col3:
            donated = sum(
                1 for d in donors if d["last"] != "None"
            )

            st.metric("Total Donations", donated)

    # -----------------------------
    # ADD DONOR
    # -----------------------------
    elif menu == "➕ Add Donor":

        st.subheader("Register Donor")

        with st.form("donor_form"):

            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Full Name")
                blood = st.selectbox("Blood Group", BLOOD_GROUPS)
                location = st.selectbox("City", PAKISTAN_CITIES)

            with col2:
                phone = st.text_input("Phone")
                email = st.text_input("Email")
                cnic = st.text_input("CNIC")

            submitted = st.form_submit_button("Register Donor")

            if submitted:

                if not validate_name(name):
                    st.error("Invalid name!")

                elif not validate_phone(phone):
                    st.error("Invalid phone number!")

                elif not validate_email(email):
                    st.error("Invalid email!")

                elif not validate_cnic(cnic):
                    st.error("Invalid CNIC!")

                else:

                    donors = read_donors()

                    existing_cnic = any(
                        d["cnic"] == cnic for d in donors
                    )

                    existing_email = any(
                        d["email"] == email for d in donors
                    )

                    if existing_cnic:
                        st.error("CNIC already exists!")

                    elif existing_email:
                        st.error("Email already exists!")

                    else:

                        donors.append({
                            "name": name,
                            "blood": blood,
                            "location": location,
                            "phone": phone,
                            "email": email,
                            "cnic": cnic,
                            "last": "None"
                        })

                        write_donors(donors)

                        st.success("Donor registered successfully!")

    # -----------------------------
    # DONATE BLOOD
    # -----------------------------
    elif menu == "🩸 Donate Blood":

        st.subheader("Record Blood Donation")

        cnic_input = st.text_input("Enter Donor CNIC")

        if st.button("Record Donation"):

            if not validate_cnic(cnic_input):
                st.error("Invalid CNIC!")

            else:

                donors = read_donors()
                found = False

                for d in donors:

                    if d["cnic"] == cnic_input:

                        found = True

                        if not is_eligible(d["last"]):

                            st.error(
                                f"{d['name']} is not eligible yet."
                            )

                        else:

                            d["last"] = datetime.date.today().strftime(
                                "%Y-%m-%d"
                            )

                            write_donors(donors)

                            st.success(
                                f"Donation recorded for {d['name']}."
                            )

                        break

                if not found:
                    st.error("Donor not found!")

    # -----------------------------
    # REQUEST BLOOD
    # -----------------------------
    elif menu == "🚨 Request Blood":

        st.subheader("Emergency Blood Request")

        required_blood = st.selectbox(
            "Required Blood Group",
            BLOOD_GROUPS
        )

        if st.button("Send Emergency Request"):

            donors = read_donors()

            eligible = [
                d for d in donors
                if d["blood"] == required_blood
                and is_eligible(d["last"])
            ]

            if not eligible:
                st.error("No eligible donors found!")

            else:

                success_count = 0

                for d in eligible:

                    email_text = f"""
Dear {d['name']},

There is an emergency blood requirement.

Blood Group: {required_blood}
Hospital: {hospital_name}

Please contact the hospital if you can donate.

Regards,
Blood Donation Network
"""

                    if send_email(
                        d["email"],
                        "Emergency Blood Donation Request",
                        email_text
                    ):
                        success_count += 1

                st.success(
                    f"Request sent to {success_count} donor(s)."
                )

    # -----------------------------
    # VIEW DONORS
    # -----------------------------
    elif menu == "👥 View Donors":

        st.subheader("Registered Donors")

        donors = read_donors()

        if donors:

            df = pd.DataFrame(donors)

            df["Eligible"] = df["last"].apply(
                lambda x: "Yes" if is_eligible(x) else "No"
            )

            st.dataframe(df, use_container_width=True)

        else:
            st.info("No donors registered.")

    # -----------------------------
    # DELETE DONOR
    # -----------------------------
    elif menu == "🗑️ Delete Donor":

        st.subheader("Delete Donor")

        cnic_input = st.text_input("Enter Donor CNIC")

        if st.button("Delete Donor"):

            if not validate_cnic(cnic_input):
                st.error("Invalid CNIC!")

            else:

                donors = read_donors()

                found = any(
                    d["cnic"] == cnic_input
                    for d in donors
                )

                if found:

                    donors = [
                        d for d in donors
                        if d["cnic"] != cnic_input
                    ]

                    write_donors(donors)

                    st.success("Donor deleted successfully!")
                    st.rerun()

                else:
                    st.error("Donor not found!")


# -----------------------------
# MAIN APP
# -----------------------------
def main():

    initialize_files()

    st.set_page_config(
        page_title="Blood Donation Network",
        page_icon="🩸",
        layout="wide"
    )

    # -----------------------------
    # CUSTOM CSS
    # -----------------------------
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: white;
            text-align: center;
            padding: 20px;
            background: linear-gradient(90deg, #DC143C, #B22222);
            border-radius: 10px;
            margin-bottom: 30px;
        }

        .stButton > button {
            width: 100%;
            background-color: #DC143C;
            color: white;
            border-radius: 8px;
            font-weight: bold;
        }

        .stButton > button:hover {
            background-color: #B22222;
        }
        </style>
    """, unsafe_allow_html=True)

    # -----------------------------
    # SESSION STATE
    # -----------------------------
    if "logged_in" not in st.session_state:

        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.session_state.user_name = None

    # -----------------------------
    # LOGIN PAGE
    # -----------------------------
    if not st.session_state.logged_in:

        st.markdown(
            '<h1 class="main-header">🩸 Blood Donation Network</h1>',
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([1, 2, 1])

        with col2:

            st.subheader("Login")

            with st.form("login_form"):

                username = st.text_input("Username")
                password = st.text_input(
                    "Password",
                    type="password"
                )

                submitted = st.form_submit_button("Login")

                if submitted:

                    user_type, user_name = verify_login(
                        username,
                        password
                    )

                    if user_type:

                        st.session_state.logged_in = True
                        st.session_state.user_type = user_type
                        st.session_state.user_name = user_name

                        st.success(f"Welcome {user_name}!")
                        st.rerun()

                    else:
                        st.error("Invalid credentials!")

        return

    # -----------------------------
    # SIDEBAR
    # -----------------------------
    st.sidebar.markdown("---")

    st.sidebar.info(
        f"Logged in as: {st.session_state.user_name}"
    )

    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.user_type = None
        st.session_state.user_name = None

        st.rerun()

    # -----------------------------
    # DASHBOARD
    # -----------------------------
    if st.session_state.user_type == "admin":
        admin_dashboard()

    elif st.session_state.user_type == "hospital":
        hospital_dashboard(st.session_state.user_name)


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    main()
