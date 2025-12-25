#!/usr/bin/env python3
"""
Granby Police Daily Journal PDF Processor
Converts PDF files into a structured pandas DataFrame.
"""

import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import PyPDF2
import fitz  # PyMuPDF for better text extraction





class GranbyPDFProcessor:
    def __init__(self, pdf_directory="granby_police_journals", verbose=True):
        self.pdf_directory = Path(pdf_directory)
        self.verbose = verbose
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        self.logger = logging.getLogger(__name__)

        if self.verbose:
            self.logger.setLevel(logging.DEBUG)
        
        # Expected columns in the DataFrame
        self.columns = [
            "CFS #",
            "Dispatch Type",
            "Call Type", 
            "Dispatch Date",
            "Dispatch Time",
            "Location",
            "Unit Id",
            "Primary Officer",
            "File Date"
        ]

        self.call_type_categories = {
            # Motor Vehicle
            # AMV - abandoned
            'MV ACCIDENT - PERSONAL INJURY': 'Motor Vehicle',
            'MV ACCIDENT - PROPERTY': 'Motor Vehicle',
            'MV COMPLAINT': 'Motor Vehicle',
            'MV STOP': 'Motor Vehicle',
            'DWI': 'Motor Vehicle',
            'PARKING VIOLATION': 'Motor Vehicle',
            'SCHOOL BUS COMPLAINT': 'Motor Vehicle',
            'SELECTIVE ENFORCEMENT': 'Motor Vehicle',
            'AMV': 'Motor Vehicle',
            'DMV': 'Motor Vehicle',
            'STOLEN MV': 'Motor Vehicle',
            'REPOSSESSED VEHICLE ENTRY': 'Motor Vehicle',
            'REGISTRATION CHECK': 'Motor Vehicle',
            'REGISTRATION AND STOLEN CHECK': 'Motor Vehicle',
            'SCHOOL TRAFFIC': 'Traffic Control',
            'TRAFFIC CONTROL': 'Traffic Control',
        
            # Administrative
            'COMMUNITY POLICING': 'Administrative',
            'FINGERPRINTING-CIVILIA': 'Administrative',
            'PISTOL PERMIT APPLICANT': 'Administrative',
            'VENDOR PERMIT': 'Administrative',
            'POLICE INFO': 'Administrative',
            'RECORDS CHECK': 'Administrative',
            'WANTS CHECK': 'Administrative',
            'OFFICER RIDE ALONG': 'Administrative',
            'TRAINING': 'Administrative',
            'SPECIAL ASSIGNMENT': 'Administrative',
            'SCHOOL DRILL': 'Administrative',
            'WORK RELATED INJURY': 'Administrative',
            'FOUND PROPERTY': 'Administrative',
            'LOST PROPERTY': 'Administrative',
            'LOST PLATE': 'Administrative',
            
            # Criminal
            'BURGLARY - INACTIVE': 'Criminal',
            'LARCENY': 'Criminal',
            'FRAUD': 'Criminal',
            'IDENTITY THEFT': 'Criminal',
            'CRIMINAL MISCHIEF': 'Criminal',
            'TRESPASS': 'Criminal',
            'ILLEGAL BURNING': 'Criminal',
            'ILLEGAL DUMPING': 'Criminal',
            'GUNSHOT': 'Criminal',
            
            # Criminal
            'DOMESTIC': 'Criminal',
            'Criminal': 'Criminal',
            'HARASSMENT': 'Criminal',
            'BREACH OF PEACE': 'Criminal',
            'WARRANT SERVICE': 'Criminal',
            'WARRANT RECEIVED': 'Criminal',
            'PROTECTIVE ORDER': 'Criminal',
            'RESTRAINING ORDER': 'Criminal',
            
            # Alarms
            'ALARM - BURGLARY': 'Alarms',
            'ALARM - FIRE': 'Alarms',
            'ALARM - ROBBERY': 'Alarms',
            'ALARM - TROUBLE/UNKNOWN': 'Alarms',
            
            # Welfare
            'CHECK ON WELFARE': 'Medical/Welfare',
            'MEDICAL ASSIST': 'Medical/Welfare',
            'LIFT ASSIST': 'Medical/Welfare',
            'MISSING PERSON': 'Medical/Welfare',
            'EMERGENCY COMMITTAL': 'Medical/Welfare',
            'EMERGENCY (OTHER THAN FIRE)': 'Medical/Welfare',
            'TRANSPORT CIVILIAN': 'Medical/Welfare',
            
            # Emergency
            'FIRE': 'Emergency',
            '911 UNKNOWN': 'Emergency',
            'SMOKE IN AREA': 'Emergency',
            'POWER OUTAGE': 'Emergency',
            'PUBLIC HAZARD': 'Emergency',
            'DAMAGE TO TOWN PROPERTY': 'Emergency',
            
            # Investigation
            'INVESTIGATION': 'Investigation',
            'FOLLOW-UP': 'Investigation',
            'SUSPICIOUS INCIDENT': 'Investigation',
            'SUSPICIOUS PERSON': 'Investigation',
            'UNKNOWN COMPLAINT': 'Investigation',
            'SUSPICIOUS MOTOR VEHICLE': 'Investigation',
            
            # Complaint
            'NOISE COMPLAINT': 'Complaint',
            'ANIMAL COMPLAINT': 'Complaint',
            'DOG COMPLAINT': 'Complaint',
            'LOITERING': 'Complaint',
            'OPEN DOOR': 'Complaint',
            'LOCKOUT': 'Complaint',
            
            # Civil/Non-Criminal
            'CIVIL MATTER': 'Civil',
            'ESCORT': 'Civil',
            
            # Inter-Agency Cooperation
            'ASSIST OUTSIDE AGENCY': 'Inter-Agency',
            'MUTUAL AID': 'Inter-Agency',
            'REGIONAL TEAM': 'Inter-Agency',
            
            # Proactive/Preventive
            'BUSINESS CHECK': 'Patrol',
            'DIRECTED FOOT PATROL': 'Patrol',
            'DIRECTED MOTOR PATROL': 'Patrol',
            'NEIGHBORHOOD CHECK': 'Patrol',
            'VACANT/VACATION HOUSE': 'Patrol',
            
            # Juvenile
            'JUVENILE': 'Juvenile',
        }
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using PyMuPDF for better formatting."""
        try:
            doc = fitz.open(str(pdf_path))
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            self.logger.warning(f"PyMuPDF failed for {pdf_path}, trying PyPDF2: {e}")
            
            # Fallback to PyPDF2
            try:
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text()
                    return text
            except Exception as e2:
                self.logger.error(f"Failed to extract text from {pdf_path}: {e2}")
                return ""
    
    def parse_date_from_filename(self, filename: str) -> str:
        """Extract date from filename in MM-DD-YYYY format."""
        match = re.search(r'(\d{2}-\d{2}-\d{4})', filename)
        if match:
            return match.group(1)
        return ""

    def parse_fingers(self, text: str) -> List[str]:
        res = re.search(r".*(FINGERPRINTIN[^\d]*)(\d.+)", text)
        if res:
            return list(res.groups())
        else:
            return [text]
    
    def clean_and_split_text(self, text: str) -> List[str]:
        """Clean the text and split into lines."""
        # Remove extra whitespace and split into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
            
        # Filter out header lines and page numbers
        filtered_lines = []
        skip_patterns = [
            r'Page \d+ of \d+',
            r'Granby Police Department',
            r'Case Incident Report',
            r'CFS #\s+Run Date:\s+Run Time:',
            r'CFS #',
            r'Run Date:',
            r'Run Time:',
            r'Time',
            r'Date',
            r'Call Type',
            r'Disp',
            r'Location',
            r'Unit Id\s+Primary Officer',
            r'Primary Officer',
            r'^\d{2}:\d{2}$',  # Time stamps alone
            r'^\d{2}/\d{2}/\d{4}$'  # Date stamps alone
        ]
        
        for line in lines:
            skip_line = False
            for pattern in skip_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    skip_line = True
                    break
            if not skip_line:
                filtered_lines.append(line)
        
        return filtered_lines

    def parse_incident_records(self, text_lines: List[str], file_date: str) -> List[Dict[str, Any]]:
        """Parse incident records from the cleaned text lines."""
        records = []
        current_record = None
        
        # Pattern to match CFS number at start of record
        cfs_pattern = r'^(\d{10})\s*'

        # Adjust for unusual sitch:
        clean_lines = [t for w in text_lines for t in self.parse_fingers(w)]
        
        for line in clean_lines:
            #print(line)
            # Check if this line starts a new record (begins with CFS number)
            cfs_match = re.match(cfs_pattern, line)
            
            if cfs_match:
                # Save previous record if exists
                if current_record:
                    records.append(current_record)
                
                # Start new record
                cfs_number = cfs_match.group(1)
                remaining_line = line[len(cfs_match.group(0)):].strip()
                
                # Parse the remaining parts of the line
                current_record = self.parse_incident_line(cfs_number, remaining_line, file_date)
                
            elif current_record:
                # This line continues the current record (multi-line location or call type)
                self.append_to_current_record(current_record, line)
        
        # Don't forget the last record
        if current_record:
            records.append(current_record)
        
        return records
    
    def parse_incident_line(self, cfs_number: str, line: str, file_date: str) -> Dict[str, Any]:
        """Initialize a record given the CFS number."""
        record = {
            "CFS #": cfs_number,
            "Dispatch Type": "",
            "Call Type": "", 
            "Dispatch Date": "",
            "Dispatch Time": "", 
            "Location": "",
            "Unit Id": "",
            "Primary Officer": "",
            "File Date": file_date
        }
    
        return record
    
    def append_to_current_record(self, record: Dict[str, Any], line: str):
        """Append continuation line to the current record."""
    
        # useful expressions
        re_date_and_time = r'^(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})'
        re_date= r'\d{2}/\d{2}/\d{4}'
        re_time= r'\d{2}:\d{2}'
        
        # Split the line by multiple spaces (assuming columns are separated by multiple spaces)
        line = line.strip()
        parts = re.split(r'\s{2,}', line)
    
        # not yet captured call type and dispatch date 
        if (record["Call Type"] == "") & (record["Dispatch Date"] == ""):
            # Check if it starts with a number (priority code) followed by 1+ spaces
            priority_match = re.match(r'^(\d{1,2})\s+(.+)', line)
            if priority_match and (re.match(re_date_and_time, line) is None):
                record["Dispatch Type"] = priority_match.group(1).strip()
                record["Call Type"] = priority_match.group(2).strip()
            elif (record["Dispatch Type"] == "") & (re.match(r'^(\d{1,2})$', line) is not None):
                record["Dispatch Type"] = line
            elif (re.match(r'^(\d{1,2})$', line) is None) and (re.match(re_date, line) is None):
                record["Call Type"] = line
    
        # likely continuation if line looks like text but have not yet parsed date and time
        elif (record["Call Type"] != "") and (record["Dispatch Date"] == "") \
             and not ((re.search(re_date, line)) or (re.search(re_time, line))):
            record["Call Type"] += " " + line

        # parse dispatch date & time only if dispatch type already known
        # must use pattern match to fill records
        if (record["Dispatch Time"] == ""):
            datetime_match = re.match(re_date_and_time, line)
            if datetime_match:
                record["Dispatch Date"] = datetime_match.group(1)
                record["Dispatch Time"] = datetime_match.group(2)
            else:
                # Sometimes just time is present
                if re.match(re_time, line):
                    record["Dispatch Time"] = re.match(re_time, line).group(1)
    
        # after processing time should be the location (not yet unit ID)
        is_location = False
        if (record['Dispatch Time'] != "") & (record['Unit Id'] == ""):
            if (not re.match(re_time, line)) & (not re.match(re_date_and_time, line)):
                is_location = True
                if record["Location"]:
                    sepr = " " if record["Location"].endswith(",") else ", "
                    record["Location"] += sepr + line.lstrip('0')
                else:
                    record["Location"] = line.lstrip('0')
    
            # pick up unit ID  
            # line ending 3 digits:
            if record['Unit Id'] == "":
                if re.match(r"\d\d\d", line[-3:]):
                    record['Unit Id'] = line[-3:]
                    record["Location"] = record["Location"][:-3]
                # line ending 3 digits like 56-6:
                elif re.match(r"\d\d-\d", line[-4:]):
                    record['Unit Id'] = line[-4:]
                    record["Location"] = record["Location"][:-4]
                # line ending Lost Acres LA34:
                elif re.match(r"LA\d\d", line[-4:]):
                    record['Unit Id'] = line[-4:]
                    record["Location"] = record["Location"][:-4]
                # line ending ALSO like 56-6:
                elif re.match(r"-ALS", line[-4:]):
                    unitid = line.split(' ')[-1]
                    lenid = len(unitid)
                    record['Unit Id'] = unitid
                    record["Location"] = record["Location"][:-lenid]
    
            # if parsing cell tower can fill this in now
            if record["Location"] == 'CELL TOWER':
                record['Unit Id'] = '999'
    
        # if have found dispatch time know it is not part of call type
        if (record["Unit Id"] == "") & (record["Dispatch Time"] != ""):
            # only a few characters, fewer than "GRANBY"
            if len(line) <= 5:
                record["Unit Id"] = line
            elif (len(line.split(',')) == 2) & (record["Primary Officer"]== "") & (not is_location):
                record["Primary Officer"] = line
    
        # If it's two words and have a unit id then is officer
        if (len(line.split(",")) == 2) & (record["Primary Officer"] == "") & (record["Unit Id"] != ""):
            if not re.search(r".+\d.+", line):
                record["Primary Officer"] = line

    
    def process_single_pdf(self, pdf_path: Path) -> List[Dict[str, Any]]:
        """Process a single PDF file and return records."""
        self.logger.debug(f"Processing {pdf_path.name}")
        
        # Extract file date from filename
        file_date = self.parse_date_from_filename(pdf_path.name)
        
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            self.logger.warning(f"No text extracted from {pdf_path.name}")
            return []
        
        # Clean and split text
        text_lines = self.clean_and_split_text(text)

        # Parse incident records
        records = self.parse_incident_records(text_lines, file_date)
        
        self.logger.debug(f"Extracted {len(records)} records from {pdf_path.name}")
        return records
    
    def process_all_pdfs(self) -> pd.DataFrame:
        """Process all PDF files in the directory and return a combined DataFrame."""
        if not self.pdf_directory.exists():
            self.logger.error(f"Directory {self.pdf_directory} does not exist")
            return pd.DataFrame(columns=self.columns)
        
        pdf_files = list(self.pdf_directory.glob("*.pdf"))
        if not pdf_files:
            self.logger.warning(f"No PDF files found in {self.pdf_directory}")
            return pd.DataFrame(columns=self.columns)
        
        self.logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        all_records = []
        
        for pdf_file in sorted(pdf_files):
            records = self.process_single_pdf(pdf_file)
            all_records.extend(records)
        
        # Create DataFrame
        df = pd.DataFrame(all_records, columns=self.columns)
        
        # Clean up the DataFrame
        df = self.clean_dataframe(df)
        
        self.logger.info(f"Created DataFrame with {len(df)} total records")
        return df

    def assign_categories(self, txt: str) -> str:
        """Assign categories"""
        return self.call_type_categories.get(txt.strip(), 'Other')
    
    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize the DataFrame."""
        # Remove empty records
        df = df.dropna(subset=["CFS #"])
        
        # Clean whitespace from all string columns
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].str.split().str.join(' ')
            df[col] = df[col].str.rstrip(',')
        
        # Convert date columns
        try:
            df['Dispatch Timestamp'] = pd.to_datetime(df['Dispatch Date'] + " " + df['Dispatch Time'], errors='coerce')
        except:
            self.logger.warning("Could not parse dispatch dates")

        try:
            df['Dispatch Date'] = pd.to_datetime(df['Dispatch Date'], errors='coerce')
        except:
            self.logger.warning("Could not parse dispatch dates")
        
        df['Dispatch Hour'] = df['Dispatch Timestamp'].dt.hour

        # Sort by date and time
        df = df.sort_values(['Dispatch Date', 'Dispatch Time'], ascending=[True, True])

        # Assign categories
        df['Call Category'] = df['Call Type'].apply(lambda x: self.assign_categories(x))

        check911 = ((df['Call Type'].str.contains('911') & (df['Primary Officer'].str.len() > 1))).astype('int')
        df['Call Type'] = df['Call Type'].where(check911 == 0, '911 RESPONSE')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df
    
    def save_to_csv(self, df: pd.DataFrame, output_file: str = "granby_police_data.csv"):
        """Save DataFrame to CSV file."""
        output_path = self.pdf_directory / output_file
        df.to_csv(output_path, index=False)
        self.logger.info(f"Data saved to {output_path}")
    
    def save_to_excel(self, df: pd.DataFrame, output_file: str = "granby_police_data.xlsx"):
        """Save DataFrame to Excel file."""
        output_path = self.pdf_directory / output_file
        df.to_excel(output_path, index=False)
        self.logger.info(f"Data saved to {output_path}")

def main():
    """Main entry point."""
    # You can customize the PDF directory here
    pdf_dir = os.path.expanduser("~/Documents/Granby_Police_Journals")
    
    processor = GranbyPDFProcessor(pdf_directory=pdf_dir)
    
    # Process all PDFs
    df = processor.process_all_pdfs()
    
    if not df.empty:
        # Display basic info
        print(f"\nProcessed {len(df)} records")
        print(f"Date range: {df['Disp Date'].min()} to {df['Disp Date'].max()}")
        print(f"Columns: {', '.join(df.columns)}")
        
        # Show sample records
        print("\nSample records:")
        print(df.head().to_string(index=False))
        
        # Save to files
        processor.save_to_csv(df)
        try:
            processor.save_to_excel(df)
        except ImportError:
            print("Excel export requires openpyxl: pip install openpyxl")
    
    return df

if __name__ == "__main__":
    result_df = main()
