from sheets_handler import SheetsHandler

try:
    s = SheetsHandler('credentials.json', '1bIH-SmBWm6nyxpvJ4fAWZIZ-99eu_m9qS-N_34VW9oE')
    s.connect()
    print("✓ Connection successful")
    print("✓ Students worksheet:", s.students_worksheet.title if s.students_worksheet else "None")
    print("✓ Logs worksheet:", s.logs_worksheet.title if s.logs_worksheet else "None")
except Exception as e:
    print(f"✗ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
