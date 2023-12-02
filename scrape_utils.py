import requests
from bs4 import BeautifulSoup
import json

# Base URL of the site we will scrape from
BASE_URL = "https://erowid.org/experiences/"


def get_substance_links(substances):
    # Retrieve the HTML content of the main page
    page = requests.get(BASE_URL)
    soup = BeautifulSoup(page.content, "html.parser")

    # Find the table by ID
    table = soup.find("table", id="exp-front-top-table")
    links = {}
    print("TABLE found")

    # Iterate through all links in the table
    for link in table.find_all("a", href=True):
        substance_name = link.text
        # If the substance is in our list, save the link
        if substance_name in substances:
            links[substance_name] = BASE_URL + link["href"]
    print("LINKS found", links)
    return links


# Function to scrape the reports of a specific substance
def scrape_substance_reports(substance_url):
    # Construct the URL for the substance page
    url = substance_url
    # Make the request and create a BeautifulSoup object
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    # Extract the trip reports - this would need to be customized according to the page structure
    reports = []
    # Example: Find all 'a' elements with a specific CSS class (this would depend on the actual structure of the page)
    report_links = soup.find_all("a", class_="report-link-class")
    for link in report_links:
        report_url = BASE_URL + link["href"]
        report_page = requests.get(report_url)
        report_soup = BeautifulSoup(report_page.content, "html.parser")

        # Again, you would need to customize the extraction process based on the structure of the individual report pages
        report_text = report_soup.find("div", class_="report-text-class").text
        reports.append(report_text)

    return reports


# Function to scrape all selected substances
def scrape_all(substances):
    all_reports = {}
    for substance in substances:
        all_reports[substance] = scrape_substance_reports(substance)
    return all_reports


# Function to save reports to a JSON file
def save_reports_to_file(reports, filename):
    with open(filename, "w") as file:
        json.dump(reports, file, indent=4)


# Main function to run the scraping process
def main(substances, output_filename):
    substance_links = get_substance_links(substances)
    all_reports = {}
    print("SUBSTANCE LINKS", substance_links)
    # Scrape reports for each substance
    for substance, url in substance_links.items():
        print("SCRAPING", substance, url)
        reports = scrape_substance_reports(url)
        all_reports[substance] = reports

    # Save the reports to a JSON file
    with open(output_filename, "w") as file:
        json.dump(all_reports, file, indent=4)


# Example usage:
substances_to_scrape = [
    "LSD",
]  # Your list of substances goes here
output_file = "trip_reports.json"
main(substances_to_scrape, output_file)
