import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import json

class SheetsHandler:
    def __init__(self, credentials_file, sheet_id):
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None
        self.students_worksheet = None
        self.logs_worksheet = None

    def connect(self):
        """Connects to Google Sheets using service account credentials."""
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            if not os.path.exists(self.credentials_file):
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_file}")
                
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, scope)
            self.client = gspread.authorize(creds)
            self.sheet = self.client.open_by_key(self.sheet_id)
            self.init_worksheets()
            print("Successfully connected to Google Sheets.")
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            raise e

    def init_worksheets(self):
        """Initializes worksheets, creating them if they don't exist."""
        try:
            self.students_worksheet = self.sheet.worksheet("Students")
        except gspread.exceptions.WorksheetNotFound:
            self.students_worksheet = self.sheet.add_worksheet(title="Students", rows="1000", cols="7")
            self.students_worksheet.append_row(["Student_ID", "Name", "Reg_No", "Section", "Ticket_ID", "Status", "Entry_Time"])

        try:
            self.logs_worksheet = self.sheet.worksheet("Scan Logs")
        except gspread.exceptions.WorksheetNotFound:
            self.logs_worksheet = self.sheet.add_worksheet(title="Scan Logs", rows="1000", cols="4")
            self.logs_worksheet.append_row(["Ticket_ID", "Scan_Time", "Gate_Type", "Result"])

    def add_students(self, students_data):
        """
        Adds a list of students to the Students worksheet.
        students_data: List of lists/tuples containing student info.
        """
        if not self.students_worksheet:
            try:
                self.connect()
            except Exception as e:
                print(f"Error connecting in add_students: {e}")
                raise
        
        # Append rows
        if self.students_worksheet:
            try:
                self.students_worksheet.append_rows(students_data)
                print(f"Successfully added {len(students_data)} students to Google Sheets")
            except Exception as e:
                print(f"Error appending rows: {e}")
                raise
        else:
            raise Exception("Could not connect to Google Sheets to add students.")

    def get_student_by_ticket(self, ticket_id):
        """Retrieves student details by Ticket ID."""
        if not self.students_worksheet:
            try:
                self.connect()
            except Exception:
                return None, None

        if not self.students_worksheet:
            return None, None

        try:
            cell = self.students_worksheet.find(ticket_id)
            if cell:
                row_values = self.students_worksheet.row_values(cell.row)
                # Map headers to values
                headers = self.students_worksheet.row_values(1)
                student = dict(zip(headers, row_values))
                return student, cell.row
            return None, None
        except gspread.exceptions.CellNotFound:
            return None, None

    def update_status(self, row_index, status, gate_type):
        """Updates the status and time for a student."""
        if not self.students_worksheet:
            self.connect()

        if self.students_worksheet:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Update Status column (F)
            self.students_worksheet.update_cell(row_index, 6, status)

            # Update Entry_Time (G)
            if gate_type == "IN":
                 self.students_worksheet.update_cell(row_index, 7, timestamp)

    def log_scan(self, ticket_id, gate_type, result):
        """Logs a scan event."""
        if not self.logs_worksheet:
            try:
                self.connect()
            except Exception:
                return

        if self.logs_worksheet:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.logs_worksheet.append_row([ticket_id, timestamp, gate_type, result])

    def get_scan_logs(self):
        """Retrieves all scan logs from the worksheet."""
        if not self.logs_worksheet:
            try:
                self.connect()
            except Exception:
                return []
        
        if not self.logs_worksheet:
            return []

        try:
            return self.logs_worksheet.get_all_records()
        except Exception as e:
            print(f"Error fetching scan logs: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_all_records(self):
        """Retrieves all student records from the worksheet."""
        if not self.students_worksheet:
            try:
                self.connect()
            except Exception:
                return []
        
        if not self.students_worksheet:
            return []

        try:
            return self.students_worksheet.get_all_records()
        except Exception as e:
            print(f"Error fetching all records: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_stats(self):
        """Returns simple statistics."""
        if not self.students_worksheet:
            try:
                self.connect()
            except Exception:
                return {"total": 0, "entered": 0, "current_inside": 0, "exited": 0}
        
        if not self.students_worksheet:
             return {"total": 0, "entered": 0, "current_inside": 0, "exited": 0}

        try:
            all_records = self.students_worksheet.get_all_records()
            total = len(all_records)
            entered = sum(1 for r in all_records if r.get("Status") == "IN")
            
            return {
                "total": total,
                "entered": entered
            }
        except Exception as e:
            print(f"Error fetching stats: {e}")
            import traceback
            traceback.print_exc()
            return {"total": 0, "entered": 0, "current_inside": 0, "exited": 0}
