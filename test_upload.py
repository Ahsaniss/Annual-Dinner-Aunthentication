from sheets_handler import SheetsHandler
import pandas as pd
import os
from utils import generate_uuid

# Create test CSV data
test_data = {
    'Student_ID': ['S001', 'S002'],
    'Name': ['Ahmed Ali', 'Zahra Khan'],
    'Reg_No': ['REG001', 'REG002'],
    'Department': ['CS', 'ENG']
}

df = pd.DataFrame(test_data)
print("Test data:")
print(df)

try:
    # Generate Ticket IDs
    df['Ticket_ID'] = [generate_uuid() for _ in range(len(df))]
    df['Status'] = 'NOT_ENTERED'
    df['Entry_Time'] = ''
    df['Exit_Time'] = ''
    
    print("\nDataframe with Ticket IDs:")
    print(df)
    
    # Convert to list of lists
    students_data = df[['Student_ID', 'Name', 'Reg_No', 'Department', 'Ticket_ID', 'Status', 'Entry_Time', 'Exit_Time']].values.tolist()
    print("\nData to upload:")
    print(students_data)
    
    # Test upload
    s = SheetsHandler('credentials.json', '1bIH-SmBWm6nyxpvJ4fAWZIZ-99eu_m9qS-N_34VW9oE')
    s.connect()
    print("\n✓ Connected to Google Sheets")
    
    s.add_students(students_data)
    print("✓ Students uploaded successfully!")
    
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}")
    print(f"Message: {e}")
    import traceback
    traceback.print_exc()
