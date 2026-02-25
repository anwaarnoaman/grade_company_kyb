import streamlit as st
import requests
from datetime import datetime
import json

# -----------------------
# Helper functions
# -----------------------
API_BASE = "http://localhost:8082"

def login(username, password):
    data = {
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "",
        "client_id": "string",
        "client_secret": "********"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(f"{API_BASE}/auth/login", data=data, headers=headers)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        st.error(response.json().get("detail", "Login failed"))
        return None

def create_company(token, company_name):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"name": company_name, "status": "active"}
    response = requests.post(f"{API_BASE}/companies/", json=payload, headers=headers)
    if response.status_code in [200, 201]:
        return response.json()
    else:
        st.error(response.text)
        return None

def upload_documents(token, company_id, files):
    headers = {"Authorization": f"Bearer {token}"}
    files_payload = [("files", (file.name, file, "application/pdf")) for file in files]
    data = {"company_id": company_id}
    response = requests.post(f"{API_BASE}/documents/upload", headers=headers, files=files_payload, data=data)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(response.text)
        return None

def generate_kyb(token, company_id):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{API_BASE}/companies/{company_id}/generate-kyb", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(response.text)
        return None

# -----------------------
# Recursive function to render/edit JSON
# -----------------------
def render_kyb_json(data, parent_key=""):
    updated = {}
    for key, value in data.items():
        full_key = f"{parent_key}.{key}" if parent_key else key
        if isinstance(value, dict):
            with st.expander(f"{full_key} (dict)"):
                updated[key] = render_kyb_json(value, full_key)
        elif isinstance(value, list):
            with st.expander(f"{full_key} (list)"):
                new_list = []
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        with st.expander(f"{key}[{i}]"):
                            new_list.append(render_kyb_json(item, f"{full_key}[{i}]"))
                    else:
                        new_val = st.text_input(f"{full_key}[{i}]", value=str(item))
                        new_list.append(new_val)
                updated[key] = new_list
        else:
            updated[key] = st.text_input(full_key, value=str(value))
    return updated

# -----------------------
# Initialize session state
# -----------------------
if "token" not in st.session_state:
    st.session_state.token = None
if "company" not in st.session_state:
    st.session_state.company = None
if "documents" not in st.session_state:
    st.session_state.documents = None
if "kyb_data" not in st.session_state:
    st.session_state.kyb_data = None
if "audit_logs" not in st.session_state:
    st.session_state.audit_logs = []

# -----------------------
# Login Screen
# -----------------------
if st.session_state.token is None:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        token = login(username, password)
        if token:
            st.session_state.token = token
            st.rerun()

# -----------------------
# Create Company Screen
# -----------------------
elif st.session_state.company is None:
    st.title("Create New Company KYB Profile")
    company_name = st.text_input("Company Name")
    if st.button("Create Company") and company_name:
        company = create_company(st.session_state.token, company_name)
        if company:
            st.session_state.company = company
            st.rerun()

# -----------------------
# Document Upload Screen
# -----------------------
elif st.session_state.documents is None:
    st.title(f"Upload Documents for {st.session_state.company['name']}")
    uploaded_files = st.file_uploader("Select PDF documents", type="pdf", accept_multiple_files=True)

    if st.button("Go Back"):
        st.session_state.company = None
        st.rerun()

    if st.button("Upload Documents") and uploaded_files:
        documents_response = upload_documents(
            st.session_state.token, st.session_state.company["company_id"], uploaded_files
        )
        if documents_response:
            st.session_state.documents = documents_response
            st.rerun()

# -----------------------
# Generate KYB & Full Review Screen
# -----------------------
else:
    st.title(f"KYB Profile for {st.session_state.company['name']}")

    if st.session_state.kyb_data is None:
        if st.button("Go Back"):
            st.session_state.documents = None
            st.rerun()

        if st.button("Generate KYB Profile"):
            kyb_result = generate_kyb(st.session_state.token, st.session_state.company["company_id"])
            if kyb_result:
                st.session_state.kyb_data = kyb_result
                st.rerun()
    else:
        kyb_unified = st.session_state.kyb_data["kyb_result"]["unified_company"]
        updated_kyb = render_kyb_json(kyb_unified)

        st.write("---")
        st.checkbox_label = "I confirm that I have reviewed the extracted information, supporting documents, and risk indicators. Submission constitutes a regulatory attestation."
        confirm = st.checkbox(st.checkbox_label)

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Go Back"):
                st.session_state.kyb_data = None
                st.rerun()
        with col2:
            if confirm and st.button("Confirm & Save"):
                st.session_state.kyb_data["kyb_result"]["unified_company"] = updated_kyb
                st.session_state.audit_logs.append({
                    "timestamp": str(datetime.utcnow()),
                    "action": "Review & Confirm",
                    "kyb_snapshot": updated_kyb
                })
                with open("final_kyb.json", "w") as f:
                    json.dump(st.session_state.kyb_data, f, indent=2)
                with open("audit_log.json", "w") as f:
                    json.dump(st.session_state.audit_logs, f, indent=2)
                st.success("KYB review confirmed and saved!")
                st.info(st.checkbox_label)