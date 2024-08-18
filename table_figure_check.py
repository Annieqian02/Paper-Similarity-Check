import os
import re
import PyPDF2
import csv

def extract_text_from_pdf(file_path):
    pdf_reader = PyPDF2.PdfReader(open(file_path, 'rb'))
    text = ''
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text

def find_largest_numbers(text):
    # Regular expressions to match "Table", "Figure", and "Appendix Table" followed by numbers
    # Exclude "Appendix Table" when searching for "Table"
    table_numbers = re.findall(r'(?<!Appendix\s)Table\s+(\d+)', text, re.IGNORECASE)
    figure_numbers = re.findall(r'Figure\s+(\d+)', text, re.IGNORECASE)
    appendix_table_numbers = re.findall(r'Appendix\s+Table\s+(\d+)', text, re.IGNORECASE)
    
    # Convert all found numbers to integers
    table_numbers = list(map(int, table_numbers))
    figure_numbers = list(map(int, figure_numbers))
    appendix_table_numbers = list(map(int, appendix_table_numbers))
    
    # Find the largest numbers, if any
    largest_table_number = max(table_numbers) if table_numbers else None
    largest_figure_number = max(figure_numbers) if figure_numbers else None
    largest_appendix_table_number = max(appendix_table_numbers) if appendix_table_numbers else None
    
    return largest_table_number, largest_figure_number, largest_appendix_table_number

def process_files_in_directory(directory_path):
    # Prepare a list to store the results
    results = []
    
    # Iterate through all PDF files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            file_path = os.path.join(directory_path, filename)
            text = extract_text_from_pdf(file_path)
            largest_table, largest_figure, largest_appendix_table = find_largest_numbers(text)
            results.append({
                'filename': filename,
                'largest_table': largest_table,
                'largest_figure': largest_figure,
                'largest_appendix_table': largest_appendix_table
            })
    
    return results

def save_results_to_csv(results, csv_file_path):
    # Specify the header for the CSV
    header = ['filename', 'largest_table', 'largest_figure', 'largest_appendix_table']
    
    # Write results to the CSV file
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        for data in results:
            writer.writerow(data)

# Example usage
directory_path = '/Users/annieqian/Desktop/check_similarity/anon'
csv_file_path = '/Users/annieqian/Desktop/check_similarity/number_tables/num_tables.csv'

# Process the files and get the results
results = process_files_in_directory(directory_path)

# Save the results to a CSV file
save_results_to_csv(results, csv_file_path)

print(f"Results have been saved to {csv_file_path}")




#directory_path = '/Users/annieqian/Desktop/check_similarity/test_1'
#csv_file_path = '/Users/annieqian/Desktop/check_similarity/number_tables/num_tables.csv'

