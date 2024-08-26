import requests
from bs4 import BeautifulSoup
import difflib
import csv
import gender_guesser.detector as gender_detector

# Replace with your actual API keys
GENDER_API_KEY = '0412ccf37ee783ac3aa0d06b31ba93a64d7935585ae312edc1c90c96d065b7ed'
NAME_API_KEY = '7a9dde4132e1aba0319187e2fd683318-user1'
NAMSOR_API_KEY = '2e090edaeada28900baf12beef494ded'

def extract_abstract_from_meta(html_content):
    """Extracts the abstract from the meta tag with name='citation_abstract'."""
    soup = BeautifulSoup(html_content, 'html.parser')
    meta_tag = soup.find('meta', {'name': 'citation_abstract'})
    if meta_tag:
        return meta_tag.get('content')
    return None

def extract_authors_from_meta(html_content):
    """Extracts author names from meta tags with name='citation_author'."""
    soup = BeautifulSoup(html_content, 'html.parser')
    author_meta_tags = soup.find_all('meta', {'name': 'citation_author'})
    authors = [tag.get('content') for tag in author_meta_tags]
    return authors

def get_related_work_url(html_content):
    """Finds the URL for the related journal article."""
    soup = BeautifulSoup(html_content, 'html.parser')
    related_works_section = soup.find('b', string="Related works:")
    
    if related_works_section:
        journal_link = related_works_section.find_next('a', href=True)
        if journal_link and "Journal Article" in journal_link.parent.text:
            return "https://econpapers.repec.org" + journal_link['href']
    
    return None

def compare_abstracts(abstract1, abstract2):
    """Compares two abstracts and returns a similarity ratio."""
    return difflib.SequenceMatcher(None, abstract1, abstract2).ratio()

def determine_gender_with_gender_guesser(first_name):
    """Determines gender using the gender-guesser library."""
    d = gender_detector.Detector()
    gender_result = d.get_gender(first_name)
    
    if gender_result in ['male', 'mostly_male']:
        return 'male'
    elif gender_result in ['female', 'mostly_female']:
        return 'female'
    else:
        return 'unknown'

def determine_gender_with_genderapi(first_name, country_code=None):
    """Determines gender using the GenderAPI with optional country localization."""
    api_url = f"https://gender-api.com/get?name={first_name}&key={GENDER_API_KEY}"
    if country_code:
        api_url += f"&country={country_code}"
    
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get('gender', 'unknown')
    return 'unknown'

def determine_gender_with_nameapi(first_name):
    """Determines gender using the NameAPI."""
    api_url = f"https://api.nameapi.org/rest/v5.3/genderizer/personalnameparser?key={NAME_API_KEY}&name={first_name}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        gender_info = data.get('gender')
        if gender_info:
            return gender_info
    return 'unknown'

def determine_gender_with_namsor(first_name, last_name=None):
    """Determines gender using the Namsor API."""
    api_url = "https://v2.namsor.com/NamSorAPIv2/api2/json/genderBatch"
    headers = {
        "X-API-KEY": NAMSOR_API_KEY,
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    data = {
        "personalNames": [
            {"firstName": first_name, "lastName": last_name}
        ]
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        if result['personalNames']:
            return result['personalNames'][0].get('likelyGender', 'unknown')
    return 'unknown'

def determine_gender(first_name, last_name=None, country_code=None):
    """Combines multiple methods to determine gender."""
    gender = determine_gender_with_gender_guesser(first_name)
    if gender == 'unknown':
        gender = determine_gender_with_genderapi(first_name, country_code)
    if gender == 'unknown':
        gender = determine_gender_with_nameapi(first_name)
    if gender == 'unknown':
        gender = determine_gender_with_namsor(first_name, last_name)
    return gender

def analyze_authors(authors):
    """Analyzes the authors list to count males, females, and unknown genders."""
    num_male = 0
    num_female = 0
    num_unknown = 0
    
    for author in authors:
        names = author.split()
        first_name = names[0]
        last_name = names[-1] if len(names) > 1 else None
        gender = determine_gender(first_name, last_name)
        if gender == 'male':
            num_male += 1
        elif gender == 'female':
            num_female += 1
        else:
            num_unknown += 1
    
    return len(authors), num_female, num_male, num_unknown

def process_paper(paper_number):
    """Processes a single NBER working paper and compares its abstract to the related journal article."""
    nber_url = f"https://econpapers.repec.org/paper/nbrnberwo/{paper_number}.htm"
    nber_response = requests.get(nber_url)
    
    if nber_response.status_code == 200:
        nber_html = nber_response.text
        
        # Extract the NBER working paper's abstract and authors
        nber_abstract = extract_abstract_from_meta(nber_html)
        nber_authors = extract_authors_from_meta(nber_html)
        
        if nber_abstract:
            # Analyze NBER authors
            nber_author_count, nber_female_count, nber_male_count, nber_unknown_count = analyze_authors(nber_authors)
            
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
                        
                        return (paper_number, nber_url, journal_url, similarity_ratio,
                                nber_author_count, nber_female_count, nber_male_count, nber_unknown_count)
                    else:
                        return (paper_number, nber_url, journal_url, "Journal abstract not found",
                                nber_author_count, nber_female_count, nber_male_count, nber_unknown_count)
                else:
                    return (paper_number, nber_url, journal_url, "Failed to fetch journal article",
                            nber_author_count, nber_female_count, nber_male_count, nber_unknown_count)
            else:
                return (paper_number, nber_url, None, "Related journal article link not found",
                        nber_author_count, nber_female_count, nber_male_count, nber_unknown_count)
        else:
            return (paper_number, nber_url, None, "NBER abstract not found",
                    "N/A", "N/A", "N/A", "N/A")
    else:
        return (paper_number, nber_url, None, "Failed to fetch NBER working paper",
                "N/A", "N/A", "N/A", "N/A")

# Prepare the CSV file
csv_file = "abstract_comparison_with_nber_authors_3.csv"
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Paper Number", "NBER URL", "Journal URL", "Similarity Ratio or Error",
                     "Number of Authors", "Number of Female Authors", "Number of Male Authors", "Number of Unknown Gender Authors"])

    # Iterate through the paper numbers from 20723 to 20822
    for paper_number in range(21201, 22201):
        result = process_paper(paper_number)
        writer.writerow(result)
        print(f"Processed paper number {paper_number}")

print(f"Results written to {csv_file}")
