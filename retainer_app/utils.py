import pandas as pd
import openpyxl
from django.core.exceptions import ValidationError
from django.core.validators import validate_email


def validate_excel_file(file_path):
    """
    Validate Excel file structure and required columns
    """
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        # Required columns
        required_columns = ['ID', 'Name', 'Email']
        optional_columns = ['Phone', 'State', 'Zip Code', 'Age', 'First Name Injured', 'Last Name Injured']
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValidationError(f"Missing required columns: {', '.join(missing_columns)}")
        
        # Validate data types and formats
        validation_errors = []
        
        for index, row in df.iterrows():
            row_num = index + 2  # Excel row number (1-indexed + header)
            
            # Validate ID
            if pd.isna(row['ID']):
                validation_errors.append(f"Row {row_num}: Missing ID")
            
            # Validate Name
            if pd.isna(row['Name']) or str(row['Name']).strip() == '':
                validation_errors.append(f"Row {row_num}: Missing Name")
            
            # Validate Email
            if pd.isna(row['Email']):
                validation_errors.append(f"Row {row_num}: Missing Email")
            else:
                try:
                    validate_email(str(row['Email']))
                except ValidationError:
                    validation_errors.append(f"Row {row_num}: Invalid email format")
            
            # Validate Age if provided
            if not pd.isna(row.get('Age', '')) and row.get('Age', '') != '':
                try:
                    age = int(row['Age'])
                    if age < 0 or age > 120:
                        validation_errors.append(f"Row {row_num}: Invalid age (must be 0-120)")
                except (ValueError, TypeError):
                    validation_errors.append(f"Row {row_num}: Age must be a number")
        
        # Return validation results
        return {
            'is_valid': len(validation_errors) == 0,
            'errors': validation_errors,
            'total_rows': len(df),
            'columns': list(df.columns)
        }
        
    except Exception as e:
        raise ValidationError(f"Error reading Excel file: {str(e)}")


def clean_excel_data(row):
    """
    Clean and normalize data from Excel row
    """
    cleaned_data = {}
    
    # Clean ID
    cleaned_data['external_id'] = str(row['ID']).strip()
    
    # Clean Name
    cleaned_data['name'] = str(row['Name']).strip()
    
    # Clean Email
    cleaned_data['email'] = str(row['Email']).strip().lower()
    
    # Clean optional fields
    cleaned_data['phone'] = str(row.get('Phone', '')).strip() if not pd.isna(row.get('Phone', '')) else ''
    cleaned_data['state'] = str(row.get('State', '')).strip() if not pd.isna(row.get('State', '')) else ''
    cleaned_data['zip_code'] = str(row.get('Zip Code', '')).strip() if not pd.isna(row.get('Zip Code', '')) else ''
    cleaned_data['first_name_injured'] = str(row.get('First Name Injured', '')).strip() if not pd.isna(row.get('First Name Injured', '')) else ''
    cleaned_data['last_name_injured'] = str(row.get('Last Name Injured', '')).strip() if not pd.isna(row.get('Last Name Injured', '')) else ''
    
    # Clean Age
    try:
        age_value = row.get('Age', '')
        if not pd.isna(age_value) and age_value != '':
            cleaned_data['age'] = int(age_value)
        else:
            cleaned_data['age'] = None
    except (ValueError, TypeError):
        cleaned_data['age'] = None
    
    return cleaned_data


def generate_external_id(recipient_id, timestamp_str):
    """
    Generate external ID for NextKeySign submission
    """
    return f"retainer_{recipient_id}_{timestamp_str}"


def format_phone_number(phone):
    """
    Format phone number for display
    """
    if not phone:
        return ''
    
    # Remove non-numeric characters
    digits = ''.join(filter(str.isdigit, phone))
    
    # Format as (XXX) XXX-XXXX if 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format


def validate_state_code(state):
    """
    Validate US state code or name
    """
    if not state:
        return True
    
    # List of valid state codes and names
    valid_states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
        'DC'  # District of Columbia
    ]
    
    return state.upper() in valid_states


def get_processing_statistics(excel_upload):
    """
    Get detailed processing statistics for an Excel upload
    """
    recipients = excel_upload.recipients.all()
    
    stats = {
        'total': recipients.count(),
        'pending': recipients.filter(status='pending').count(),
        'submitted': recipients.filter(status='submitted').count(),
        'completed': recipients.filter(status='completed').count(),
        'failed': recipients.filter(status='failed').count(),
        'skipped': recipients.filter(status='skipped').count(),
    }
    
    # Calculate percentages
    if stats['total'] > 0:
        for key in ['pending', 'submitted', 'completed', 'failed', 'skipped']:
            stats[f'{key}_percentage'] = round((stats[key] / stats['total']) * 100, 2)
    else:
        for key in ['pending', 'submitted', 'completed', 'failed', 'skipped']:
            stats[f'{key}_percentage'] = 0
    
    return stats
