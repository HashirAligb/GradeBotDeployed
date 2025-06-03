import csv
import json
from collections import defaultdict

def normalize_term(term):
    """Normalize term format to FA/SP + YY format"""
    term = term.strip().upper()
    if 'FALL' in term or term.startswith('F'):
        # Extract year, handle both YYYY and YY
        year_part = ''.join(filter(str.isdigit, term))
        if len(year_part) >= 2:
             return f"FA{year_part[-2:]}"
        
    elif 'SPRING' in term or term.startswith('S'):
         # Extract year, handle both YYYY and YY
        year_part = ''.join(filter(str.isdigit, term))
        if len(year_part) >= 2:
             return f"SP{year_part[-2:]}"

    return term

def normalize_column_headers(headers):
    """Normalize column headers to a standard format"""
    header_map = {
        'TERM': 'term',
        'Term': 'term',
        'SUBJECT': 'subject',
        'NBR': 'course_number',
        'Course Number': 'course_number',
        'PROF': 'professor',
        'Instructor': 'instructor', # Keep instructor as is for now, prof will be used for key
        'AVG GPA': 'avg_gpa',
        'Average GPA': 'avg_gpa',
        'INC/NA': 'inc_na',
        'Inc/No Grade': 'inc_na',
        'W': 'W',
        'Withdrawal': 'W'
    }
    # Process headers: remove newlines, strip whitespace, then map and lowercase (except for grades)
    cleaned_headers = [h.replace('\n', '').strip() for h in headers]
    
    grades_to_preserve_case = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'W', 'P', 'INC/NA', 'inc_na']
    
    return [header_map.get(h, h if h in grades_to_preserve_case else h.lower()) for h in cleaned_headers]

def parse_grades(csv_file):
    """Parse the CSV file and return normalized grade data"""
    current_block_rows = []
    all_data_blocks = []
    current_headers = None

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        
        for row in reader:
            if not any(row):  # Empty row indicates block separator
                if current_block_rows:
                    if current_headers:
                         all_data_blocks.append((current_headers, current_block_rows))
                    current_block_rows = []
                    current_headers = None # Reset headers for the next block
            elif any(cell.strip() for cell in row):
                 # Check if this row is a header row
                 if any(cell.strip().upper().replace('\n', '') in ('TERM', 'Term') for cell in row):
                     if current_block_rows and current_headers:
                          all_data_blocks.append((current_headers, current_block_rows))

                     current_headers = normalize_column_headers(row)
                     current_block_rows = [] # Start a new block of rows under this header
                 elif current_headers:
                      # Only add row if we have headers for the current block
                     current_block_rows.append(row)

        # Add the last block if it exists
        if current_block_rows and current_headers:
            all_data_blocks.append((current_headers, current_block_rows))

    # Process all blocks and create normalized data
    result = {}
    
    for headers, rows in all_data_blocks:
        # Dynamically detect which grade columns are present in this block
        possible_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'W', 'P', 'INC/NA', 'inc_na']
        # Ensure grade columns from headers match the desired output keys (preserve case for grades)
        grade_columns = [h for h in headers if h in possible_grades]

        for i, row in enumerate(rows):
            # Ensure row has enough columns to match headers
            if len(row) < len(headers):
                continue
                
            data = dict(zip(headers, row))
            
            # Skip non-CSCI courses
            if data.get('subject', '').upper() != 'CSCI':
                continue
                
            # Create key for the result dictionary
            term = normalize_term(data.get('term', ''))
            # Use either 'professor' or 'instructor' for the professor name, preferring 'professor' if both exist
            prof = data.get('professor', data.get('instructor','')).strip()
            course = data.get('course_number', '').strip()
            
            if not all([term, prof, course]):
                continue
                
            key = f"{prof}, {course}, {term}"
            
            # Extract grade data only for columns present in this block
            grades = {}
            for grade in grade_columns:
                value = data.get(grade, '0')
                try:
                    grades[grade] = int(value)
                except (ValueError, TypeError):
                    grades[grade] = 0

            # For output, ensure all standard grades are present (fill missing with 0)
            standard_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'W', 'P', 'INC/NA']
            final_grades = {}
            for g in standard_grades:
                 final_grades[g] = grades.get(g, 0)

            # Handle 'inc_na' specifically if present in grades (could be from either 'INC/NA' or 'inc_na' in headers)
            if 'inc_na' in grades:
                 final_grades['INC/NA'] = grades['inc_na']
            elif 'INC/NA' not in final_grades:
                 final_grades['INC/NA'] = 0


            # Get average GPA
            try:
                avg_gpa = float(data.get('avg_gpa', '0'))
            except (ValueError, TypeError):
                avg_gpa = 0.0

            # Only add if the key doesn't exist (to avoid potential duplicates or summary rows)
            if key not in result:
                 result[key] = {
                    "name": prof,
                    "term": term,
                    "course": course,
                    "grades": final_grades,
                    "avg_gpa": avg_gpa
                }

    
    return result

def main():
    input_file = "CSCI_ALL - Sheet1.csv"
    output_file = "grades.json"
    
    try:
        data = parse_grades(input_file)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"Successfully processed {len(data)} course sections")
        print(f"Data written to {output_file}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main() 