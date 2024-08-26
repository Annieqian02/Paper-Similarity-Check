import requests
from bs4 import BeautifulSoup

def extract_authors_from_meta(html_content):
    """Extracts author names from meta tags with name='citation_author'."""
    soup = BeautifulSoup(html_content, 'html.parser')
    author_meta_tags = soup.find_all('meta', {'name': 'citation_author'})
    authors = [tag.get('content') for tag in author_meta_tags]
    return authors

def determine_gender_using_genderize(first_name):
    """Determines gender using the Genderize.io API."""
    api_url = f"https://api.genderize.io?name={first_name}"
    response = requests.get(api_url)
    if response.status_code == 200:
        data = response.json()
        return data.get('gender', 'unknown')
    return 'unknown'

# Fetch the NBER working paper page
url = "https://econpapers.repec.org/paper/nbrnberwo/20822.htm"
response = requests.get(url)

if response.status_code == 200:
    html_content = response.text
    
    # Extract the author names
    authors = extract_authors_from_meta(html_content)
    number_of_authors = len(authors)
    
    print(f"Number of Authors: {number_of_authors}")
    print("Author Names and Guessed Genders:")
    for author in authors:
        first_name = author.split()[0]
        author_gender = determine_gender_using_genderize(first_name)
        print(f"{author}: {author_gender}")
else:
    print(f"Failed to fetch the page. Status code: {response.status_code}")
