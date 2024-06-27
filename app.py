import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from firebase_config import auth, db
import time


# Google Sheets authentication
scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file('gsheets-424112-059d537a0191.json', scopes=scope)
client = gspread.authorize(creds)

# Function to read data from a Google Sheet
def read_sheet(sheet_name):
    sheet = client.open_by_key('1lZPO8TKrFynWEwA2NSTo4eNMj9EUyK4AlB7G5tvZzck').worksheet(sheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Function to append data to a Google Sheet
def append_to_sheet(sheet_name, df):
    sheet = client.open_by_key('1lZPO8TKrFynWEwA2NSTo4eNMj9EUyK4AlB7G5tvZzck').worksheet(sheet_name)
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
    if st.button("Back"):
        st.session_state.page = 'login'
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
    if st.button("Retracted Requests"):
        st.session_state.page = 'retracted_requests'
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
    if 'reference_details' not in st.session_state:
        st.session_state.reference_details = {}
    if 'mail_id' not in st.session_state:
        st.session_state.mail_id = ''
    if 'checkbox_states' not in st.session_state:
        st.session_state.checkbox_states = {}
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 0

    # Back button
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Input for Opportunity_ID
    opp_id = st.text_input("Opportunity_ID", value=st.session_state.opp_id)
    st.session_state.opp_id = opp_id

    if len(opp_id) == 3:
        data = read_sheet('Sheet1')

        # Add 'Select' column if it doesn't exist
        if 'Select' not in data.columns:
            data['Select'] = False

        # Pagination
        items_per_page = 500
        total_pages = (len(data) // items_per_page) + 1

        # Display pagination controls
        st.write(f"Page {st.session_state.current_page + 1} of {total_pages}")
        if st.session_state.current_page > 0:
            if st.button("Previous"):
                st.session_state.current_page -= 1
                st.rerun()
        if st.session_state.current_page < total_pages - 1:
            if st.button("Next"):
                st.session_state.current_page += 1
                st.rerun()

        # Get the data for the current page
        start_idx = st.session_state.current_page * items_per_page
        end_idx = start_idx + items_per_page
        page_data = data.iloc[start_idx:end_idx]

        # Create a grid of checkboxes above the table
        num_checkboxes = len(page_data)
        num_columns = 15  # Number of checkboxes per row
        num_rows = (num_checkboxes // num_columns) + 1

        for row in range(num_rows):
            cols = st.columns(num_columns)
            for col in range(num_columns):
                index = row * num_columns + col
                if index < num_checkboxes:
                    with cols[col]:
                        checkbox_key = f"row_{start_idx + index}"
                        checkbox_state = st.session_state.checkbox_states.get(checkbox_key, False)
                        checkbox = st.checkbox("✔", key=checkbox_key, value=checkbox_state, label_visibility="collapsed")
                        st.write(f"{start_idx + index + 1}")
                        page_data.at[page_data.index[index], 'Select'] = checkbox
                        st.session_state.checkbox_states[checkbox_key] = checkbox

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

        # Filter data based on selected filters
        filtered_data = page_data
        if selected_filters:
            filtered_data = page_data[page_data['Specific_HRC_Products'].str.contains('|'.join(selected_filters))]

        # Display the table with checkboxes
        st.write("Select rows and submit:")
        st.write(filtered_data)

        # Update the selected rows in session state
        for idx in filtered_data.index:
            if filtered_data.at[idx, 'Select']:
                if idx not in st.session_state.selected_rows:
                    st.session_state.selected_rows.append(idx)
            else:
                if idx in st.session_state.selected_rows:
                    st.session_state.selected_rows.remove(idx)

        # Create a DataFrame for selected rows
        selected_df = data.loc[st.session_state.selected_rows].copy()
        if not selected_df.empty:
            if 'Select' in selected_df.columns:
                selected_df.drop(columns=['Select'], inplace=True)
            selected_df.insert(0, 'Opportunity_ID', opp_id)
            selected_df.insert(4, 'Requester_Mail', '') # Add a blank column for requester's email
            selected_df['Reference Request Details'] = '' # Add a new column for reference request details
            selected_df = selected_df[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Reference Request Details']]

            # Display the selected rows
            st.write("Selected Rows:")
            st.write(selected_df)

            # Ask user for mail id
            mail_id = st.text_input("Enter your mail ID")
            if mail_id or st.button("Add Mail"):
                selected_df['Requester_Mail'] = mail_id
                # Ask user for reference request details for each row
                all_details_filled = True
                for idx in selected_df.index:
                    reference_detail = st.text_input(f"Reference Request Details for row {idx} - WHEN do they want the call by? AGENDA items for the call? WHO would the call be with?", key=f"reference_detail_{idx}")
                    if not reference_detail:
                        all_details_filled = False
                    selected_df.at[idx, 'Reference Request Details'] = reference_detail

                # Display the entered email and reference details immediately
                st.write("Selected Rows with Requester Mail and Reference Request Details:")
                st.write(selected_df)

                if st.button("Submit") and all_details_filled:
                    append_to_sheet('Sheet2', selected_df)
                    st.success("Data has been submitted successfully.")
                    st.session_state.selected_rows = [] # clear selected rows
                    st.session_state.opp_id = '' # clear Opportunity_ID
                    st.session_state.selected_filters = [] # clear selected filters
                    st.session_state.checkbox_states = {} # clear checkbox states

                    # Store data in Firebase Realtime Database (excluding 'Reference Request Details')
                    store_data_in_firebase(selected_df.drop(columns=['Reference Request Details']))

                    # Redirect to the requester page after a delay
                    time.sleep(3)
                    st.session_state.page = 'requester'
                    st.rerun()
                elif not all_details_filled:
                    st.error("Please fill in all the reference request details for each row.")
    




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
            row = {key: (value if pd.notna(value) else '') for key, value in row.items()}  # Ensure no NaN values

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

    if st.button("Pending Approvals"):
        st.session_state.page = 'pending_approvals'
        st.rerun()

    if st.button("Accepted and Rejected Approvals"):
        st.session_state.page = 'accepted_rejected_approvals'
        st.rerun()


def pending_approvals_page():
    st.title("Pending Approvals")
    if st.button("Back"):
        st.session_state.page = 'main'
        st.rerun()

    st.write("Approver Table:")
    approver_data = fetch_approver_data()

    if not approver_data.empty:
        # Ensure the 'Approval Status' and 'Extra Comments' columns exist and initialize with default values where not present
        if 'Approval Status' not in approver_data.columns:
            approver_data['Approval Status'] = 'No Response'  # Set a default value
        else:
            approver_data['Approval Status'].fillna('No Response', inplace=True)  # Replace NaN with default value

        if 'Extra Comments' not in approver_data.columns:
            approver_data['Extra Comments'] = ''  # Set a default value
        else:
            approver_data['Extra Comments'].fillna('', inplace=True)  # Replace NaN with default value

        # Display the table with necessary columns including 'Approval Status' and 'Extra Comments'
        display_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Approval Status', 'Extra Comments']
        approver_data = approver_data.reindex(columns=display_columns)

        # Adding Approval Status, Extra Comments, and Submit Response columns
        for idx, row in approver_data.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                approval_status = row['Approval Status']
                selected_status = st.selectbox(
                    f"Approval Status for row {idx}",
                    [
                        'No Response',
                        'Request Received',
                        'More Information Required',
                        'Approver Rejects - Not Going to Ask Client',
                        'Approver Accepts - Client Feedback Pending',
                        'Client Rejects',
                        'Client Approves'
                    ],
                    index=0 if approval_status not in [
                        'No Response',
                        'Request Received',
                        'More Information Required',
                        'Approver Rejects - Not Going to Ask Client',
                        'Approver Accepts - Client Feedback Pending',
                        'Client Rejects',
                        'Client Approves'
                    ] else [
                        'No Response',
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
                extra_comments = st.text_input(f"Extra Comments for row {idx}", value=row['Extra Comments'], key=f'extra_comments_{idx}')
            with col3:
                if st.button(f"Submit Response for row {idx}", key=f'submit_{idx}'):
                    if selected_status in ['More Information Required', 'Approver Rejects - Not Going to Ask Client', 'Client Rejects'] and not extra_comments:
                        st.error(f"Extra Comments are required for row {idx} when status is '{selected_status}'")
                    else:
                        update_approval_status(idx, selected_status, extra_comments)
                        st.success(f"Approval Status for row {idx} updated successfully!")
                        approver_data.at[idx, 'Approval Status'] = selected_status  # Update the DataFrame
                        approver_data.at[idx, 'Extra Comments'] = extra_comments  # Update the DataFrame

        # Display the table with the updated approval status and extra comments
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
                approver_df = pd.DataFrame(approver_data)
            else:
                approver_df = pd.DataFrame(approver_data.values())
            # Remove duplicate rows based on all columns
            approver_df.drop_duplicates(inplace=True)
            return approver_df
    return pd.DataFrame()


def update_pending_requests(row):
    try:
        requester_mail = row['Requester_Mail']
        account_name = row['Account_Name']
        opportunity_id = row['Opportunity_ID']
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        requester_id = None
        for uid, user_info in users.items():
            if user_info['email'] == requester_mail:
                requester_id = uid
                break

        if requester_id:
            # Fetch the pending requests data
            pending_data = db.child('pendingRequests').child(requester_id).get(id_token).val()
            if pending_data:
                if isinstance(pending_data, list):
                    pending_df = pd.DataFrame(pending_data)
                else:
                    pending_df = pd.DataFrame(pending_data.values())

                # Ensure 'Update from the Approver' and 'Extra Comments' columns exist
                if 'Update from the Approver' not in pending_df.columns:
                    pending_df['Update from the Approver'] = 'No Response'
                if 'Extra Comments' not in pending_df.columns:
                    pending_df['Extra Comments'] = 'None'

                # Find the matching row in the pending requests
                match_idx = pending_df[(pending_df['Opportunity_ID'] == opportunity_id) &
                                       (pending_df['Account_Name'] == account_name) &
                                       (pending_df['Owner_Mail'] == row['Owner_Mail'])].index
                if not match_idx.empty:
                    # Update the specific row's 'Update from the Approver' and 'Extra Comments'
                    pending_df.at[match_idx[0], 'Update from the Approver'] = row.get('Approval Status', 'No Response')
                    pending_df.at[match_idx[0], 'Extra Comments'] = row.get('Extra Comments', 'None')

                # Convert DataFrame to a list of dictionaries
                pending_dict = pending_df.fillna('').to_dict(orient='records')

                # Update the 'pendingRequests' node with the updated DataFrame
                db.child('pendingRequests').child(requester_id).set(pending_dict, id_token)
    except Exception as e:
        st.error(f"Error updating pending requests: {e}")


def update_approval_status(row_idx, status, extra_comments):
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
                    # Update the specific row's approval status and extra comments
                    approver_df.at[row_idx, 'Approval Status'] = status
                    if status in ['More Information Required', 'Approver Rejects - Not Going to Ask Client', 'Client Rejects']:
                        approver_df.at[row_idx, 'Extra Comments'] = extra_comments
                    else:
                        approver_df.at[row_idx, 'Extra Comments'] = 'None'

                    # Replace <NA> values with empty strings
                    approver_df = approver_df.fillna('')

                    # Convert the entire DataFrame to a dictionary
                    updated_data = approver_df.to_dict(orient='records')

                    # Update the entire approverRequests node with the updated DataFrame
                    db.child('approverRequests').child(user_id).set(updated_data, id_token)

                    # Append the updated row to 'Sheet3'
                    append_to_sheet('Sheet3', approver_df.iloc[[row_idx]])

                    # Update the 'Pending Raised Requests' with 'Extra Comments'
                    update_pending_requests(approver_df.iloc[row_idx])

                    # Move the row to 'acceptedRequests' or 'rejectedRequests' based on the status
                    if status == 'Client Approves':
                        move_to_accepted_requests(approver_df.iloc[row_idx])
                    elif status in ['Client Rejects', 'Approver Rejects - Not Going to Ask Client']:
                        move_to_rejected_requests(approver_df.iloc[row_idx])

                    # Move the row to 'acceptedRejectedApprovals' based on the status
                    if status in ['Client Approves', 'Client Rejects', 'Approver Rejects - Not Going to Ask Client']:
                        move_to_accepted_rejected_approvals(approver_df.iloc[row_idx])
                        approver_df = approver_df.drop(row_idx).reset_index(drop=True)
                        updated_data = approver_df.to_dict(orient='records')
                        db.child('approverRequests').child(user_id).set(updated_data, id_token)

    except Exception as e:
        st.error(f"Error updating approval status: {e}")





def move_to_accepted_rejected_approvals(row):
    try:
        id_token = st.session_state.user['idToken']
        # Add the row to 'acceptedRejectedApprovals'
        row_dict = row.to_dict()
        db.child('acceptedRejectedApprovals').push(row_dict, id_token)
    except Exception as e:
        st.error(f"Error moving to accepted and rejected approvals: {e}")

def fetch_accepted_rejected_approvals_data():
    id_token = st.session_state.user['idToken']
    accepted_rejected_data = db.child('acceptedRejectedApprovals').get(id_token).val()
    if accepted_rejected_data:
        if isinstance(accepted_rejected_data, list):
            accepted_rejected_df = pd.DataFrame(accepted_rejected_data)
        else:
            accepted_rejected_df = pd.DataFrame(accepted_rejected_data.values())
        return accepted_rejected_df
    return pd.DataFrame()

def accepted_rejected_approvals_page():
    st.title("Accepted and Rejected Approvals")
    if st.button("Back"):
        st.session_state.page = 'approver'
        st.rerun()

    # Fetch and display accepted and rejected approvals
    accepted_rejected_data = fetch_accepted_rejected_approvals_data()
    if not accepted_rejected_data.empty:
        # Ensure correct column order and add 'Update from the Approver' and 'Extra Comments' columns if they don't exist
        required_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Approval Status', 'Extra Comments']
        for col in required_columns:
            if col not in accepted_rejected_data.columns:
                accepted_rejected_data[col] = '' # Add missing columns with default empty values

        # Ensure correct column order
        accepted_rejected_data = accepted_rejected_data[required_columns]

        st.table(accepted_rejected_data)
    else:
        st.write("No accepted or rejected approvals to display.")



def move_to_rejected_requests(row):
    try:
        requester_mail = row['Requester_Mail']
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        requester_id = None
        for uid, user_info in users.items():
            if user_info['email'] == requester_mail:
                requester_id = uid
                break

        if requester_id:
            # Remove the row from 'pendingRequests'
            pending_data = db.child('pendingRequests').child(requester_id).get(id_token).val()
            if pending_data:
                if isinstance(pending_data, list):
                    pending_df = pd.DataFrame(pending_data)
                else:
                    pending_df = pd.DataFrame(pending_data.values())

                # Find the matching row in the pending requests
                match_idx = pending_df[(pending_df['Opportunity_ID'] == row['Opportunity_ID']) &
                                       (pending_df['Owner_Mail'] == row['Owner_Mail'])].index
                if not match_idx.empty:
                    pending_df.drop(match_idx[0], inplace=True)

                # Convert DataFrame to a list of dictionaries
                pending_dict = pending_df.to_dict(orient='records')

                # Update the 'pendingRequests' node with the updated DataFrame
                db.child('pendingRequests').child(requester_id).set(pending_dict, id_token)

                # Add the row to 'rejectedRequests', including the rejection reason
                row_dict = row.to_dict()
                row_dict['Update from the Approver'] = row['Approval Status']
                row_dict['Extra Comments'] = row['Extra Comments']
                db.child('rejectedRequests').child(requester_id).push(row_dict, id_token)
    except Exception as e:
        st.error(f"Error moving to rejected requests: {e}")


def move_to_accepted_requests(row):
    try:
        requester_mail = row['Requester_Mail']
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        requester_id = None
        for uid, user_info in users.items():
            if user_info['email'] == requester_mail:
                requester_id = uid
                break

        if requester_id:
            # Remove the row from 'pendingRequests'
            pending_data = db.child('pendingRequests').child(requester_id).get(id_token).val()
            if pending_data:
                if isinstance(pending_data, list):
                    pending_df = pd.DataFrame(pending_data)
                else:
                    pending_df = pd.DataFrame(pending_data.values())

                # Find the matching row in the pending requests
                match_idx = pending_df[(pending_df['Opportunity_ID'] == row['Opportunity_ID']) &
                                       (pending_df['Owner_Mail'] == row['Owner_Mail'])].index
                if not match_idx.empty:
                    pending_df.drop(match_idx[0], inplace=True)

                # Convert DataFrame to a list of dictionaries
                pending_dict = pending_df.to_dict(orient='records')

                # Update the 'pendingRequests' node with the updated DataFrame
                db.child('pendingRequests').child(requester_id).set(pending_dict, id_token)

                # Add the row to 'acceptedRequests', including the approval status
                row_dict = row.to_dict()
                row_dict['Update from the Approver'] = 'Client Approves'
                if 'Extra Comments' in row_dict:
                    del row_dict['Extra Comments']  # Remove 'Extra Comments' from the row dictionary
                db.child('acceptedRequests').child(requester_id).push(row_dict, id_token)
    except Exception as e:
        st.error(f"Error moving to accepted requests: {e}")



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
        # Ensure correct column order and add 'Update from the Approver' and 'Extra Comments' columns
        pending_data = pending_data[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver', 'Extra Comments']]

        # Add 'Retract' option and 'Reason to Retract' input
        for idx, row in pending_data.iterrows():
            cols = st.columns([3, 2, 1])
            with cols[0]:
                st.write(row['Opportunity_ID'])
            with cols[1]:
                reason = st.text_input(f"Reason to Retract for row {idx}", key=f'reason_{idx}')
            with cols[2]:
                if st.button(f"Retract for row {idx}", key=f'retract_{idx}'):
                    if not reason:
                        st.error(f"Reason to Retract is required for row {idx}")
                    else:
                        retract_request(row, reason)
                        st.success(f"Request retracted for row {idx}")
                        st.rerun()

        st.table(pending_data)

def retract_request(row, reason):
    try:
        requester_mail = row['Requester_Mail']
        owner_mail = row['Owner_Mail']
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        requester_id = None
        owner_id = None
        for uid, user_info in users.items():
            if user_info['email'] == requester_mail:
                requester_id = uid
            if user_info['email'] == owner_mail:
                owner_id = uid

        if requester_id:
            # Remove the row from 'pendingRequests'
            pending_data = db.child('pendingRequests').child(requester_id).get(id_token).val()
            if pending_data:
                if isinstance(pending_data, list):
                    pending_df = pd.DataFrame(pending_data)
                else:
                    pending_df = pd.DataFrame(pending_data.values())

                # Find the matching row in the pending requests
                match_idx = pending_df[(pending_df['Opportunity_ID'] == row['Opportunity_ID']) & (pending_df['Owner_Mail'] == row['Owner_Mail'])].index
                if not match_idx.empty:
                    pending_df.drop(match_idx[0], inplace=True)

                # Convert DataFrame to a list of dictionaries
                pending_dict = pending_df.fillna('').to_dict(orient='records')

                # Update the 'pendingRequests' node with the updated DataFrame
                db.child('pendingRequests').child(requester_id).set(pending_dict, id_token)

                # Add the row to 'retractedRequests', including the reason
                row_dict = row.to_dict()
                row_dict['Reason'] = reason
                db.child('retractedRequests').child(requester_id).push(row_dict, id_token)

                # Append the row to the 'Retracted Requests' worksheet
                retracted_df = pd.DataFrame([row_dict])
                append_to_sheet('Retracted Requests', retracted_df)

        if owner_id:
            # Remove the row from 'approverRequests'
            approver_data = db.child('approverRequests').child(owner_id).get(id_token).val()
            if approver_data:
                if isinstance(approver_data, list):
                    approver_df = pd.DataFrame(approver_data)
                else:
                    approver_df = pd.DataFrame(approver_data.values())

                # Find the matching row in the approver requests
                match_idx = approver_df[(approver_df['Opportunity_ID'] == row['Opportunity_ID']) & (approver_df['Requester_Mail'] == row['Requester_Mail'])].index
                if not match_idx.empty:
                    approver_df.drop(match_idx[0], inplace=True)

                # Convert DataFrame to a list of dictionaries
                approver_dict = approver_df.fillna('').to_dict(orient='records')

                # Update the 'approverRequests' node with the updated DataFrame
                db.child('approverRequests').child(owner_id).set(approver_dict, id_token)

                # Add the row to 'retractedApproverRequests'
                row_dict = row.to_dict()
                row_dict['Reason'] = reason
                db.child('retractedApproverRequests').child(owner_id).push(row_dict, id_token)

    except Exception as e:
        st.error(f"Error retracting request: {e}")

def retracted_requests_page():
    st.title("Retracted Requests")
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Fetch and display retracted requests for the requester
    retracted_data = fetch_retracted_requests_data()
    if not retracted_data.empty:
        # Ensure correct column order and add 'Reason' column if it doesn't exist
        required_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Reason']
        for col in required_columns:
            if col not in retracted_data.columns:
                retracted_data[col] = ''  # Add missing columns with default empty values

        # Ensure correct column order
        retracted_data = retracted_data[required_columns]

        st.table(retracted_data)
    else:
        st.write("No retracted requests to display.")

def fetch_retracted_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        retracted_data = db.child('retractedRequests').child(user_id).get(id_token).val()
        if retracted_data:
            if isinstance(retracted_data, list):
                retracted_df = pd.DataFrame(retracted_data)
            else:
                retracted_df = pd.DataFrame(retracted_data.values())
            return retracted_df
    return pd.DataFrame()

def retracted_approver_requests_page():
    st.title("Retracted Requests")
    if st.button("Back"):
        st.session_state.page = 'approver'
        st.rerun()

    # Fetch and display retracted requests for the approver
    retracted_data = fetch_retracted_approver_requests_data()
    if not retracted_data.empty:
        # Ensure correct column order and add 'Reason' column if it doesn't exist
        required_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Reason']
        for col in required_columns:
            if col not in retracted_data.columns:
                retracted_data[col] = ''  # Add missing columns with default empty values

        # Ensure correct column order
        retracted_data = retracted_data[required_columns]

        st.table(retracted_data)
    else:
        st.write("No retracted requests to display.")

def fetch_retracted_approver_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        retracted_data = db.child('retractedApproverRequests').child(user_id).get(id_token).val()
        if retracted_data:
            if isinstance(retracted_data, list):
                retracted_df = pd.DataFrame(retracted_data)
            else:
                retracted_df = pd.DataFrame(retracted_data.values())
            return retracted_df
    return pd.DataFrame()


# Retracted Requests page
def retracted_requests_page():
    st.title("Retracted Requests")
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Fetch and display retracted requests
    retracted_data = fetch_retracted_requests_data()
    if not retracted_data.empty:
        # Ensure correct column order and add 'Reason' column if it doesn't exist
        required_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Reason']
        for col in required_columns:
            if col not in retracted_data.columns:
                retracted_data[col] = '' # Add missing columns with default empty values

        # Ensure correct column order
        retracted_data = retracted_data[required_columns]

        st.table(retracted_data)
    else:
        st.write("No retracted requests to display.")

def fetch_retracted_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        retracted_data = db.child('retractedRequests').child(user_id).get(id_token).val()
        if retracted_data:
            if isinstance(retracted_data, list):
                retracted_df = pd.DataFrame(retracted_data)
            else:
                retracted_df = pd.DataFrame(retracted_data.values())
            return retracted_df
    return pd.DataFrame()

def accepted_requests_page():
    st.title("Accepted Raised Requests")

    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Fetch and display accepted requests
    accepted_data = fetch_accepted_requests_data()
    if not accepted_data.empty:
        # Ensure correct column order and add 'Update from the Approver' column if it doesn't exist
        required_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver', 'Proceed with Reference Call?', 'Comments for not proceeding']
        for col in required_columns:
            if col not in accepted_data.columns:
                accepted_data[col] = ''  # Add missing columns with default empty values

        # Ensure correct column order
        accepted_data = accepted_data[required_columns]

        # Add 'Proceed with Reference Call?' and 'Comments for not proceeding' columns if they don't exist
        if 'Proceed with Reference Call?' not in accepted_data.columns:
            accepted_data['Proceed with Reference Call?'] = 'No decision taken'
        if 'Comments for not proceeding' not in accepted_data.columns:
            accepted_data['Comments for not proceeding'] = 'None'

        # Display dropdown and submit button for each row
        for idx, row in accepted_data.iterrows():
            cols = st.columns([3, 1])  # Adjust column widths as needed

            # Dropdown for 'Proceed with Reference Call?'
            proceed_with_call = cols[0].selectbox(
                f"Proceed with Reference Call? for row {idx}",
                ['No decision taken', 'Will move forward with reference call', 'Will Not move forward with reference call'],
                index=['No decision taken', 'Will move forward with reference call', 'Will Not move forward with reference call'].index(row['Proceed with Reference Call?']),
                key=f'proceed_with_call_{idx}'
            )

            # Text input for 'Comments for not proceeding' if 'Will Not move forward with reference call' is selected
            comments = row['Comments for not proceeding']
            if proceed_with_call == 'Will Not move forward with reference call':
                comments = st.text_input(f"Comments for not proceeding for row {idx}", value=row['Comments for not proceeding'], key=f'comments_{idx}')
                if not comments:
                    st.error(f"Comments are required for row {idx} when 'Will Not move forward with reference call' is selected")
            elif proceed_with_call == 'Will move forward with reference call':
                comments = 'None'

            # Submit button for each row
            if cols[1].button(f"Submit for row {idx}", key=f'submit_{idx}'):
                if proceed_with_call == 'Will Not move forward with reference call' and not comments:
                    st.error(f"Comments are required for row {idx} when 'Will Not move forward with reference call' is selected")
                else:
                    accepted_data.at[idx, 'Proceed with Reference Call?'] = proceed_with_call
                    accepted_data.at[idx, 'Comments for not proceeding'] = comments

                    # Append the updated row to 'Sheet4'
                    selected_row = accepted_data.loc[[idx]].copy()
                    append_to_sheet('Sheet4', selected_row)
                    st.success(f"Row {idx} has been appended to Sheet4.")

                    # Update the database with the new data
                    update_accepted_requests_in_db(selected_row)

        # Display the updated table with proper headings
        st.write("Accepted Requests with Proper Headings:")
        st.table(accepted_data[['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver', 'Proceed with Reference Call?', 'Comments for not proceeding']])

    else:
        st.write("No accepted requests to display.")

def update_accepted_requests_in_db(row):
    try:
        requester_mail = row['Requester_Mail'].values[0]
        id_token = st.session_state.user['idToken']
        users = db.child('users').get(id_token).val()
        requester_id = None
        for uid, user_info in users.items():
            if user_info['email'] == requester_mail:
                requester_id = uid
                break

        if requester_id:
            # Fetch the accepted requests data
            accepted_data = db.child('acceptedRequests').child(requester_id).get(id_token).val()
            if accepted_data:
                if isinstance(accepted_data, list):
                    accepted_df = pd.DataFrame(accepted_data)
                else:
                    accepted_df = pd.DataFrame(accepted_data.values())

                # Find the matching row in the accepted requests
                match_idx = accepted_df[(accepted_df['Opportunity_ID'] == row['Opportunity_ID'].values[0]) &
                                        (accepted_df['Owner_Mail'] == row['Owner_Mail'].values[0])].index
                if not match_idx.empty:
                    # Update the specific row's 'Proceed with Reference Call?' and 'Comments for not proceeding'
                    accepted_df.at[match_idx[0], 'Proceed with Reference Call?'] = row['Proceed with Reference Call?'].values[0]
                    accepted_df.at[match_idx[0], 'Comments for not proceeding'] = row['Comments for not proceeding'].values[0]

                # Convert DataFrame to a list of dictionaries
                accepted_df = accepted_df.fillna('')
                accepted_dict = accepted_df.to_dict(orient='records')

                # Update the 'acceptedRequests' node with the updated DataFrame
                db.child('acceptedRequests').child(requester_id).set(accepted_dict, id_token)
    except Exception as e:
        st.error(f"Error updating accepted requests: {e}")



def fetch_accepted_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        accepted_data = db.child('acceptedRequests').child(user_id).get(id_token).val()
        if accepted_data:
            if isinstance(accepted_data, list):
                accepted_df = pd.DataFrame(accepted_data)
            else:
                accepted_df = pd.DataFrame(accepted_data.values())
            # Ensure 'Update from the Approver' column exists
            if 'Update from the Approver' not in accepted_df.columns:
                accepted_df['Update from the Approver'] = ''
            return accepted_df
    return pd.DataFrame()



def fetch_accepted_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        accepted_data = db.child('acceptedRequests').child(user_id).get(id_token).val()
        if accepted_data:
            if isinstance(accepted_data, list):
                accepted_df = pd.DataFrame(accepted_data)
            else:
                accepted_df = pd.DataFrame(accepted_data.values())
            # Ensure 'Update from the Approver' column exists
            if 'Update from the Approver' not in accepted_df.columns:
                accepted_df['Update from the Approver'] = ''
            # Ensure 'Comments for not proceeding' column exists and set default value to 'None'
            if 'Comments for not proceeding' not in accepted_df.columns:
                accepted_df['Comments for not proceeding'] = 'None'
            return accepted_df
    return pd.DataFrame()






# Rejected Raised Requests page
def rejected_requests_page():
    st.title("Rejected Raised Requests")
    if st.button("Back"):
        st.session_state.page = 'requester'
        st.rerun()

    # Fetch and display rejected requests
    rejected_data = fetch_rejected_requests_data()
    if not rejected_data.empty:
        # Ensure correct column order and add 'Update from the Approver' and 'Extra Comments' columns if they don't exist
        required_columns = ['Opportunity_ID', 'Account_Name', 'Account_Owner', 'Owner_Mail', 'Requester_Mail', 'Update from the Approver', 'Extra Comments']
        for col in required_columns:
            if col not in rejected_data.columns:
                rejected_data[col] = ''  # Add missing columns with default empty values

        # Ensure correct column order
        rejected_data = rejected_data[required_columns]

        st.table(rejected_data)
    else:
        st.write("No rejected requests to display.")


def fetch_rejected_requests_data():
    user_email = st.session_state.user['email']
    id_token = st.session_state.user['idToken']
    users = db.child('users').get(id_token).val()
    user_id = None
    for uid, user_info in users.items():
        if user_info['email'] == user_email:
            user_id = uid
            break
    if user_id:
        rejected_data = db.child('rejectedRequests').child(user_id).get(id_token).val()
        if rejected_data:
            if isinstance(rejected_data, list):
                rejected_df = pd.DataFrame(rejected_data)
            else:
                rejected_df = pd.DataFrame(rejected_data.values())
            # Add 'Extra Comments' column if it's missing
            if 'Extra Comments' not in rejected_df.columns:
                rejected_df['Extra Comments'] = ''
            return rejected_df
    return pd.DataFrame()


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
            # Add 'Update from the Approver' and 'Extra Comments' columns if they're missing
            if 'Update from the Approver' not in pending_df.columns:
                pending_df['Update from the Approver'] = ''
            if 'Extra Comments' not in pending_df.columns:
                pending_df['Extra Comments'] = ''
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
            st.error("Invalid credentials, Please try again.")


# Main function to control the flow

def main():
    if st.session_state.page == 'login':
        login_page()
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
    elif st.session_state.page == 'pending_approvals':
        pending_approvals_page()
    elif st.session_state.page == 'accepted_rejected_approvals':
        accepted_rejected_approvals_page()
    elif st.session_state.page == 'retracted_requests':
        retracted_requests_page()

if __name__ == "__main__":
    main()
