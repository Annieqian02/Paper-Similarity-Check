import requests
from bs4 import BeautifulSoup
import difflib
import csv

def extract_abstract_from_meta(html_content):
    """Extracts the abstract from the meta tag with name='citation_abstract'."""
    soup = BeautifulSoup(html_content, 'html.parser')
    meta_tag = soup.find('meta', {'name': 'citation_abstract'})
    if meta_tag:
        return meta_tag.get('content')
    return None

def get_related_work_url(html_content):
    """Finds the URL for the related journal article."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the "Related works:" section
    related_works_section = soup.find('b', string="Related works:")
    
    if related_works_section:
        # Look for the next <a> tag after the "Related works:" section that mentions "Journal Article"
        journal_link = related_works_section.find_next('a', href=True)
        if journal_link and "Journal Article" in journal_link.parent.text:
            # Manually construct the full URL
            return "https://econpapers.repec.org" + journal_link['href']
    
    return None

def compare_abstracts(abstract1, abstract2):
    """Compares two abstracts and returns a similarity ratio."""
    return difflib.SequenceMatcher(None, abstract1, abstract2).ratio()

def process_paper(paper_number):
    """Processes a single NBER working paper and compares its abstract to the related journal article."""
    nber_url = f"https://econpapers.repec.org/paper/nbrnberwo/{paper_number}.htm"
    nber_response = requests.get(nber_url)
    
    if nber_response.status_code == 200:
        nber_html = nber_response.text
        
        # Extract the NBER working paper's abstract
        nber_abstract = extract_abstract_from_meta(nber_html)
        
        if nber_abstract:
            # Find the related journal article link
            journal_url = get_related_work_url(nber_html)
            if journal_url:
                journal_response = requests.get(journal_url)
                
                if journal_response.status_code == 200:
                    journal_html = journal_response.text
                    journal_abstract = extract_abstract_from_meta(journal_html)
                    
                    if journal_abstract:
                        # Compare the abstracts
                        similarity_ratio = compare_abstracts(nber_abstract, journal_abstract)
                        return (paper_number, nber_url, journal_url, similarity_ratio)
                    else:
                        return (paper_number, nber_url, journal_url, "Journal abstract not found")
                else:
                    return (paper_number, nber_url, journal_url, "Failed to fetch journal article")
            else:
                return (paper_number, nber_url, None, "Related journal article link not found")
        else:
            return (paper_number, nber_url, None, "NBER abstract not found")
    else:
        return (paper_number, nber_url, None, "Failed to fetch NBER working paper")

# Prepare the CSV file
csv_file = "abstract_comparison_results.csv"
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Paper Number", "NBER URL", "Journal URL", "Similarity Ratio or Error"])

    # Iterate through the paper numbers from 20723 to 20822
    for paper_number in range(20723, 20823):
        result = process_paper(paper_number)
        writer.writerow(result)
        print(f"Processed paper number {paper_number}")

print(f"Results written to {csv_file}")
