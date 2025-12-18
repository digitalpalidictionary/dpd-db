import requests


def update_content(query):
    # Replace 'http://localhost:8000' with the URL of your Flask app
    # and '/your_endpoint' with the actual endpoint that serves the updated content
    url = f"http://127.0.0.1:8000/?query={query}"
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # The response.text contains the HTML content returned by your Flask app
        html_content = response.text
        print(html_content)
        # Here you can process the HTML content as needed
        # For example, you might want to save it to a file or display it in a browser
    else:
        print(f"Failed to fetch content. Status code: {response.status_code}")


# Example usage
if __name__ == "__main__":
    query = "katena"  # Your query here
    update_content(query)
