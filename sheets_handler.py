import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os
import json
import base64
import tempfile

class SheetsHandler:
    def __init__(self, credentials_file, sheet_id):
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.client = None
        self.sheet = None
        self.students_worksheet = None
        self.logs_worksheet = None
        self.temp_creds_file = None

    def _resolve_credentials_file(self):
        """Resolve the credential path relative to this project if needed."""
        if os.path.isabs(self.credentials_file):
            return self.credentials_file

        module_dir = os.path.dirname(os.path.abspath(__file__))
        project_path = os.path.join(module_dir, self.credentials_file)
        if os.path.exists(project_path):
            return project_path

        return self.credentials_file

    def _load_credentials_from_env(self):
        """Load service account credentials from environment variables."""
        creds_json_env = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_JSON')
        creds_b64_env = os.environ.get('GOOGLE_SHEETS_CREDENTIALS_B64')

        if creds_json_env:
            try:
                creds_dict = json.loads(creds_json_env)
            except json.JSONDecodeError as exc:
                raise ValueError("Invalid JSON in GOOGLE_SHEETS_CREDENTIALS_JSON environment variable") from exc
        elif creds_b64_env:
            try:
                decoded = base64.b64decode(creds_b64_env).decode('utf-8')
                creds_dict = json.loads(decoded)
            except Exception as exc:
                raise ValueError("Invalid base64 JSON in GOOGLE_SHEETS_CREDENTIALS_B64 environment variable") from exc
        else:
            return None

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(creds_dict, f)
            self.temp_creds_file = f.name
            print(f"Using credentials from environment variable (temp file: {self.temp_creds_file})")
            return self.temp_creds_file

    def connect(self):
        """Connects to Google Sheets using service account credentials."""
        try:
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            creds_file_to_use = self._resolve_credentials_file()
            
            # Check if credentials file exists
            if not os.path.exists(creds_file_to_use):
                env_creds_file = self._load_credentials_from_env()
                if env_creds_file:
                    creds_file_to_use = env_creds_file
                else:
                    raise FileNotFoundError(
                        f"Credentials file not found: {creds_file_to_use} and neither GOOGLE_SHEETS_CREDENTIALS_JSON nor GOOGLE_SHEETS_CREDENTIALS_B64 env vars are set"
                    )
                
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file_to_use, scope)
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

    def __del__(self):
        """Cleanup temporary credentials file if it was created."""
        if self.temp_creds_file and os.path.exists(self.temp_creds_file):
            try:
                os.remove(self.temp_creds_file)
                print(f"Cleaned up temporary credentials file: {self.temp_creds_file}")
            except Exception as e:
                print(f"Error cleaning up temp credentials file: {e}")
