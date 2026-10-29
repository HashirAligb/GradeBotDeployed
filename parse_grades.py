"""Offline step that turns the messy grades CSV into grades.json.
Run it by hand (python parse_grades.py) whenever the CSV changes.
bot.py only ever reads grades.json, never the CSV."""

import csv
import json
from collections import defaultdict

def normalize_term(term):
    """Turns a term like 'Fall 2023' or 'F23' into 'FA23', or 'Spring 2024' into 'SP24'.
    The CSV writes terms a few different ways, so this keeps the json keys consistent.
    Called by parse_grades() when it builds each key."""
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
    """Takes a raw header row and returns cleaned names like 'term', 'professor', 'avg_gpa'.
    Different blocks in the CSV label the same column differently, so this maps them to one name.
    Called by parse_grades() every time it finds a header row."""
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
    # different blocks use different header names, so clean them up and map to one set of names
    # (grade columns like A+, B- keep their case, everything else gets lowercased)
    cleaned_headers = [h.replace('\n', '').strip() for h in headers]
    
    grades_to_preserve_case = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F', 'W', 'P', 'INC/NA', 'inc_na']
    
    return [header_map.get(h, h if h in grades_to_preserve_case else h.lower()) for h in cleaned_headers]

def parse_grades(csv_file):
    """Reads the CSV and returns a dict keyed by "PROF, COURSE, TERM" with grade counts and avg GPA.
    This is the cleanup step, so the bot never has to deal with the messy CSV.
    Called by main(), which writes the result to grades.json."""
    # the CSV is really several tables stacked on top of each other, each with its own header row,
    # so we read it in blocks and keep each block's headers with its rows
    current_block_rows = []
    all_data_blocks = []
    current_headers = None

    with open(csv_file, 'r') as f:
        reader = csv.reader(f)
        
        for row in reader:
            if not any(row):  # a blank row ends the current block, so save it and start fresh
                if current_block_rows:
                    if current_headers:
                         all_data_blocks.append((current_headers, current_block_rows))
                    current_block_rows = []
                    current_headers = None # Reset headers for the next block
            elif any(cell.strip() for cell in row):
                 # any row with a TERM cell is a header row, and it starts a new block
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


            # avg GPA is taken from the CSV as-is, not calculated from the grade counts
            try:
                avg_gpa = float(data.get('avg_gpa', '0'))
            except (ValueError, TypeError):
                avg_gpa = 0.0

            # first row wins: if the key is already there, skip this row (avoids duplicates and summary rows)
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
    """Runs parse_grades() on the CSV and writes the result to grades.json.
    This is what runs when you do python parse_grades.py.
    Rerun it whenever the CSV changes, since bot.py only reads the json."""
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