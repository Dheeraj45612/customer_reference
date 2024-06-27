import streamlit as st
import pandas as pd
import gspread
# from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from firebase_config import auth, db

# Google Sheets authentication
SCOPES = [ 
          "https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive.file", 
          "https://www.googleapis.com/auth/drive"]
REDIRECT_URI = 'http://localhost:8501/'
# Function to get OAuth 2.0 credentials
def get_oauth2_creds():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials1.json', SCOPES, redirect_uri=REDIRECT_URI)
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.write(f'Please go to this URL: {auth_url}')
            auth_code = st.text_input('Enter the authorization code:')
            if auth_code:
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds


creds = get_oauth2_creds()
# Check if creds is None
if creds is None:
    st.error("Failed to obtain credentials. Please try again.")
else:
    client = gspread.authorize(creds)

# Function to read data from a Google Sheet
def read_sheet(sheet_name):
    sheet = client.open_by_key('1-5Xn8hHoJQGhv5hXmXcTDXDtAvd1ybaVyjQxTrUXETc').worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Function to append data to a Google Sheet
def append_to_sheet(sheet_name, df):
    sheet = client.open_by_key('1-5Xn8hHoJQGhv5hXmXcTDXDtAvd1ybaVyjQxTrUXETc').worksheet(sheet_name)
    sheet.append_rows(df.values.tolist())

# Initialize session state variables
if 'page' not in st.session_state:
    st.session_state.page = 'login'
if 'selected_rows' not in st.session_state:
    st.session_state.selected_rows = []
if 'user' not in st.session_state:
    st.session_state.user = None

# Main page
def main_page():
    st.title("User Roles")
    if st.button("Requester"):
        st.session_state.page = 'requester'
        st.rerun()
    if st.button("Approver"):
        st.session_state.page = 'approver'
        st.rerun()

# Requester page
def requester_page():
    st.title("Requester Actions")
    if st.button("Raise a Request"):
        st.session_state.page = 'raise_request'
        st.rerun()
    if st.button("Pending Raised Requests"):
        st.session_state.page = 'pending_requests'
        st.rerun()
    if st.button("Accepted Raised Requests"):
        st.session_state.page = 'accepted_requests'
        st.rerun()
    if st.button("Rejected Raised Requests"):
        st.session_state.page = 'rejected_requests'
        st.rerun()
    if st.button("Back"):
        st.session_state.page = 'main'
        st.rerun()


# Raise a Request page
def raise_request_page():
    st.title("Raise a Request")

    # Initialize session state variables if not already done
    if 'opp_id' not in st.session_state:
        st.session_state.opp_id = ''
    if 'selected_filters' not in st.session_state:
        st.session_state.selected_filters = []
    if 'selected_rows' not in st.session_state:
        st.session_state.selected_rows = []

    # Back button
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Input for Opportunity_ID
    opp_id = st.text_input("Opportunity_ID", value=st.session_state.opp_id)
    st.session_state.opp_id = opp_id

    if len(opp_id) == 3:
        # Display checkboxes horizontally
        st.write("Filter by Specific HRC Products:")
        columns = st.columns(5)
        caa_checkbox = columns[0].checkbox("CAA", value='CAA' in st.session_state.selected_filters)
        dms_checkbox = columns[1].checkbox("DMS", value='DMS' in st.session_state.selected_filters)
        cls_checkbox = columns[2].checkbox("CLS", value='CLS' in st.session_state.selected_filters)
        crd_checkbox = columns[3].checkbox("CRD", value='CRD' in st.session_state.selected_filters)
        eipp_checkbox = columns[4].checkbox("EIPP", value='EIPP' in st.session_state.selected_filters)

        # Get the selected filters
        selected_filters = []
        if caa_checkbox:
            selected_filters.append("CAA")
        if dms_checkbox:
            selected_filters.append("DMS")
        if cls_checkbox:
            selected_filters.append("CLS")
        if crd_checkbox:
            selected_filters.append("CRD")
        if eipp_checkbox:
            selected_filters.append("EIPP")

        # Store the selected filters in session state
        st.session_state.selected_filters = selected_filters

        # Fetch data from Sheet1
        data = read_sheet('Sheet1')

        # Filter data based on selected filters
        filtered_data = data
        if selected_filters:
            filtered_data = data[data['Specific_HRC_Products'].str.contains('|'.join(selected_filters))]

        # Display filtered data
        st.write("Select rows and submit:")

        # Create a set of selected row values for easy removal
        selected_rows_set = set(st.session_state.selected_rows)

        for idx, row in filtered_data.iterrows():
            row_checkbox = st.checkbox("Select Row {}".format(idx), key=f"row_{idx}", value=tuple(row.values) in selected_rows_set)
            row_values = tuple(row.values)  # Convert Series to tuple for comparison
            if row_checkbox:
                if row_values not in selected_rows_set:
                    st.session_state.selected_rows.append(row_values)
                    selected_rows_set.add(row_values)
            else:
                if row_values in selected_rows_set:
                    st.session_state.selected_rows.remove(row_values)
                    selected_rows_set.remove(row_values)

            row_df = pd.DataFrame([row])
            row_df.index = [idx]  # set the index to match row id
            st.write(row_df)

        # Create a table to display selected rows
        if st.session_state.selected_rows:
            selected_df = pd.DataFrame(st.session_state.selected_rows, columns=data.columns)
            selected_df.drop_duplicates(inplace=True)  # Remove duplicate rows
            selected_df.reset_index(drop=True, inplace=True)  # Reset index after dropping duplicates
            selected_df.insert(0, 'Opportunity_ID', opp_id)
            selected_df.insert(4, 'Requester_Mail', '')  # Add a blank column for requester's email
            selected_df = selected_df[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail']]
            st.write("Selected Rows:")
            selected_rows_table = st.empty()  # Create an empty container for the table
            selected_rows_table.write(selected_df)  # Write the table to the container

            # Ask user for mail id
            mail_id = st.text_input("Enter your mail ID")
            if mail_id or st.button("Add Mail"):
                selected_df['Requester_Mail'] = mail_id

                # Clear the previous table
                selected_rows_table.empty()

                # Display the entered email immediately
                st.write("Selected Rows with Requester Mail:")
                st.write(selected_df)

                if st.button("Submit"):
                    append_to_sheet('Sheet2', selected_df)
                    st.success("Data has been submitted successfully.")
                    st.session_state.selected_rows = []  # clear selected rows
                    st.session_state.opp_id = '' # clear Opportunity_ID
                    st.session_state.selected_filters = [] # clear selected filters
                    
                    # Store data in Firebase Realtime Database
                    store_data_in_firebase(selected_df)

                    # Redirect to the requester page
                    st.session_state.page = 'requester'
                    st.rerun()





# Function to store data in Firebase Realtime Database
def store_data_in_firebase(data):
    try:
        # Convert DataFrame to list of dictionaries
        data_list = data.to_dict(orient='records')
        # Get the user's authentication token
        id_token = st.session_state.user['idToken']
        # Debug: Print data being sent to Firebase
        print("Data to be sent to Firebase:", data_list)
        # Push data to 'totalRequests' in Firebase
        new_request_ref = db.child('totalRequests').push(data_list, id_token)
        st.success("Data stored in Firebase successfully.")

        # Append data to approver and pending requests
        append_to_approver_and_pending_requests(data_list, id_token)
    except Exception as e:
        st.error(f"Error in store_data_in_firebase: {e}")

# Function to append data to approver and pending requests
def append_to_approver_and_pending_requests(data_list, id_token):
    try:
        users = db.child('users').get(id_token).val()

        # Check if users is None
        if users is None:
            st.error("No users found in the database. Ensure the 'users' node exists and is populated.")
            return

        for row in data_list:
            owner_mail = row['Owner_Mail']
            requester_mail = row['Requester_Mail']

            for user_id, user_info in users.items():
                if user_info['email'] == owner_mail:
                    db.child('approverRequests').child(user_id).push(row, id_token)
                elif user_info['email'] == requester_mail:
                    db.child('pendingRequests').child(user_id).push(row, id_token)
    except Exception as e:
        st.error(f"Error in append_to_approver_and_pending_requests: {e}")

def approver_page():
    st.title("Approver Actions")
    if st.button("Back"):
        st.session_state.page = 'main'
        st.rerun()

    st.write("Approver Table:")
    approver_data = fetch_approver_data()

    if not approver_data.empty:
        # Ensure the 'Approval Status' column exists and initialize with <NA> where not present
        if 'Approval Status' not in approver_data.columns:
            approver_data['Approval Status'] = pd.NA

        # Display the table with necessary columns including 'Approval Status'
        display_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Approval Status']
        approver_data = approver_data.reindex(columns=display_columns)

        # Adding Approval Status and Submit Response columns
        for idx, row in approver_data.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                approval_status = row['Approval Status']
                selected_status = st.selectbox(
                    f"Approval Status for row {idx}",
                    [
                        'Request Received',
                        'More Information Required',
                        'Approver Rejects - Not Going to Ask Client',
                        'Approver Accepts - Client Feedback Pending',
                        'Client Rejects',
                        'Client Approves'
                    ],
                    index=0 if pd.isna(approval_status) else [
                        'Request Received',
                        'More Information Required',
                        'Approver Rejects - Not Going to Ask Client',
                        'Approver Accepts - Client Feedback Pending',
                        'Client Rejects',
                        'Client Approves'
                    ].index(approval_status),
                    key=f'status_{idx}'
                )
            with col2:
                if st.button(f"Submit Response for row {idx}", key=f'submit_{idx}'):
                    update_approval_status(idx, selected_status)
                    st.success(f"Approval Status for row {idx} updated successfully!")
                    approver_data.at[idx, 'Approval Status'] = selected_status # Update the DataFrame

        # Display the table with the updated approval status
        st.write("Approver Table:")
        st.table(approver_data[display_columns])
    else:
        st.write("No requests to approve.")


def fetch_approver_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        approver_data = db.child('approverRequests').child(user_id).get(id_token).val()
        if approver_data:
            if isinstance(approver_data, list):
                return pd.DataFrame(approver_data)
            else:
                return pd.DataFrame(approver_data.values())
    return pd.DataFrame()



# Function to update the approval status in Firebase
def update_approval_status(row_idx, status):
    try:
        user_email = st.session_state.user['email']
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        user_id = None
        for uid, user_info in users.items():
            if user_info['email'] == user_email:
                user_id = uid
                break
        if user_id:
            # Fetch the approver request data
            approver_data = db.child('approverRequests').child(user_id).get(id_token).val()
            if approver_data:
                # Convert to DataFrame for easy access
                if isinstance(approver_data, list):
                    approver_df = pd.DataFrame(approver_data)
                else:
                    approver_df = pd.DataFrame(approver_data.values())

                if 0 <= row_idx < len(approver_df):
                    # Update the specific row's approval status
                    approver_df.at[row_idx, 'Approval Status'] = status
                    # Convert the updated DataFrame back to dictionary format
                    approver_dict = approver_df.to_dict(orient='records')
                    # Push the updated DataFrame back to Firebase
                    db.child('approverRequests').child(user_id).set(approver_dict, id_token)

                    # Append the updated row to 'Sheet3'
                    append_to_sheet('Sheet3', approver_df.iloc[[row_idx]])

                    # Update the 'Pending Raised Requests'
                    update_pending_requests(approver_df.iloc[row_idx])
    except Exception as e:
        st.error(f"Error updating approval status: {e}")


# Function to update the pending requests in Firebase
def update_pending_requests(updated_row):
    try:
        requester_mail = updated_row['Requester_Mail']
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        requester_id = None
        for uid, user_info in users.items():
            if user_info['email'] == requester_mail:
                requester_id = uid
                break
        if requester_id:
            pending_data = db.child('pendingRequests').child(requester_id).get(id_token).val()
            if pending_data:
                if isinstance(pending_data, list):
                    pending_df = pd.DataFrame(pending_data)
                else:
                    pending_df = pd.DataFrame(pending_data.values())

                # Find the matching row in the pending requests
                match_idx = pending_df[(pending_df['Opportunity_ID'] == updated_row['Opportunity_ID']) &
                                      (pending_df['Owner_Mail'] == updated_row['Owner_Mail'])].index
                if not match_idx.empty:
                    # Update the 'Update from the Approver' column
                    pending_df.at[match_idx[0], 'Update from the Approver'] = updated_row['Approval Status']
                    # Push the updated DataFrame back to Firebase
                    pending_dict = pending_df.to_dict(orient='records')
                    print("Pending Data to be sent to Firebase:", pending_dict)  # Debug statement
                    db.child('pendingRequests').child(requester_id).set(pending_dict, id_token)
    except Exception as e:
        st.error(f"Error updating pending requests: {e}")


# Pending Raised Requests page
def pending_requests_page():
    st.title("Pending Raised Requests")
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Display Pending Requests Table
    st.write("Pending Requests Table:")
    pending_data = fetch_pending_requests_data()
    if not pending_data.empty:
        # Ensure correct column order and add 'Update from the Approver' column
        pending_data = pending_data[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver']]
        st.table(pending_data)


# Accepted Raised Requests page
def accepted_requests_page():
    st.title("Accepted Raised Requests")

    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Fetch and display accepted requests
    pending_data = fetch_pending_requests_data()
    accepted_requests = pending_data[pending_data['Update from the Approver'] == 'Client Approves']

    if not accepted_requests.empty:
        # Ensure correct column order
        accepted_requests = accepted_requests[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver']]

        # Add 'Proceed with Reference Call?' and 'Mail to Approver' columns
        accepted_requests['Proceed with Reference Call?'] = ''
        accepted_requests['Mail to Approver'] = ''

        # Display the table with new columns
        st.write("Accepted Requests:")
        for idx, row in accepted_requests.iterrows():
            cols = st.columns([1, 1, 1, 1, 1, 1, 2, 1])  # Adjust column widths as needed
            cols[0].write(row['Opportunity_ID'])
            cols[1].write(row['Account_Name'])
            cols[2].write(row['Account_Owner'])
            cols[3].write(row['Owner_Mail'])
            cols[4].write(row['Requester_Mail'])
            cols[5].write(row['Update from the Approver'])

            # Dropdown for 'Proceed with Reference Call?'
            accepted_requests.at[idx, 'Proceed with Reference Call?'] = cols[6].selectbox(
                f"Proceed with Reference Call? for row {idx}",
                ['Will move forward with reference call', 'Will Not move forward with reference call'],
                key=f'reference_call_{idx}'
            )

            # Submit button for 'Mail to Approver'
            if cols[7].button(f"Submit for row {idx}", key=f'submit_{idx}'):
                # Check if the index exists before accessing it
                if idx in accepted_requests.index:
                    # Append the selected row to 'Sheet4'
                    selected_row = accepted_requests.loc[[idx]].copy()
                    append_to_sheet('Sheet4', selected_row)
                    st.success(f"Row {idx} has been appended to Sheet4.")
                else:
                    st.error(f"Index {idx} is out of bounds for the DataFrame.")

        # Display the updated table with proper headings
        st.write("Accepted Requests with Proper Headings:")
        st.table(accepted_requests[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver', 'Proceed with Reference Call?', 'Mail to Approver']])

    else:
        st.write("No accepted requests to display.")



# Rejected Raised Requests page
def rejected_requests_page():
    st.title("Rejected Raised Requests")
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Fetch and display rejected requests
    pending_data = fetch_pending_requests_data()
    rejected_requests = pending_data[pending_data['Update from the Approver'].isin(['Approver Rejects - Not Going to Ask Client', 'Client Rejects'])]
    if not rejected_requests.empty:
        # Ensure correct column order and add 'Update from the Approver' column
        rejected_requests = rejected_requests[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver']]
        st.table(rejected_requests)


# Function to fetch pending requests data from Firebase
def fetch_pending_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        pending_data = db.child('pendingRequests').child(user_id).get(id_token).val()
        if pending_data:
            if isinstance(pending_data, list):
                pending_df = pd.DataFrame(pending_data)
            else:
                pending_df = pd.DataFrame(pending_data.values())
            # Add 'Update from the Approver' column if it's missing
            if 'Update from the Approver' not in pending_df.columns:
                pending_df['Update from the Approver'] = ''
            return pending_df
    return pd.DataFrame()


# Login page
def login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            st.session_state.user = user
            st.session_state.page = 'main'
            st.success("Login successful!")
            st.rerun()  # Automatically navigate to the main page
        except Exception as e:
            st.error(f"Error: {e}")


# Main function to control the flow
def main():
    if st.session_state.page == 'login':
        login_page()
    # elif st.session_state.page == 'register':
    #     register_page()
    elif st.session_state.page == 'main':
        main_page()
    elif st.session_state.page == 'requester':
        requester_page()
    elif st.session_state.page == 'raise_request':
        raise_request_page()
    elif st.session_state.page == 'approver':
        approver_page()
    elif st.session_state.page == 'pending_requests':
        pending_requests_page()
    elif st.session_state.page == 'accepted_requests':
        accepted_requests_page()
    elif st.session_state.page == 'rejected_requests':
        rejected_requests_page()

if __name__ == "__main__":
    main()
