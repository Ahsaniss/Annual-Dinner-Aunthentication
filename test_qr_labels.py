import os
import sys
# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import generate_qr_code

def test_qr_generation():
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_output')
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    test_data = "TEST-TICKET-123"
    test_name = "John Doe"
    test_id = "SID001"
    
    output_path = os.path.join(test_dir, "test_qr_labeled.png")
    
    print(f"Generating QR code with labels at: {output_path}")
    generate_qr_code(
        test_data, 
        output_path=output_path, 
        name=test_name, 
        student_id=test_id
    )
    
    if os.path.exists(output_path):
        print("Success: Test QR code generated with labels.")
    else:
        print("Failure: Test QR code not found.")

if __name__ == "__main__":
    test_qr_generation()
