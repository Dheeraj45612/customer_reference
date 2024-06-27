import streamlit as st
from firebase_config import auth, db  # Assuming firebase_config.py holds authentication details

# Registration page
def register_page():
    st.title("Register")
    name = st.text_input("Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Submit"):
        if not name:
            st.error("Name is required")
        elif not email:
            st.error("Email is required")
        elif not password or not confirm_password:
            st.error("Password and Confirm Password are required")
        elif password != confirm_password:
            st.error("Passwords do not match")
        else:
            try:
                user = auth.create_user_with_email_and_password(email, password)
                st.success("User registered successfully!")

                # Store user details in the database
                user_data = {
                    "name": name,
                    "email": email,
                    "user_id": user['localId']
                }
                id_token = user['idToken']
                db.child("users").child(user['localId']).set(user_data, id_token)

            except Exception as e:
                st.error(f"Error: {e}")

# Main function to control the flow
def main():
    register_page()

if __name__ == "__main__":
    main()
