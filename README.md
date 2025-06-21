# AI-Powered SEO Content Generator for GitHub Pages

This project automates the creation and uploading of SEO-focused astrology articles to a GitHub Pages site. It uses Google's Gemini API to generate content based on a list of keywords and then pushes the generated articles as Jekyll-compatible blog posts to a specified GitHub repository.

It also automatically maintains an `index.md` file that serves as a homepage, listing all published articles.

## Features

-   **Automated Content Generation**: Leverages the Gemini API to create unique articles for any given astrology-related keyword.
-   **Optimized for GitHub Pages**: Creates posts in the `_posts` directory with the correct `YYYY-MM-DD-title.md` format for Jekyll.
-   **Automatic Indexing**: Automatically creates and updates a main `index.md` file with a list of all articles, perfect for a blog-style homepage.
-   **Bulk Processing**: Reads a list of keywords from `keywords.txt` and processes them in a batch.
-   **GitHub Integration**: Automatically creates or updates files in the specified GitHub repository.

## Prerequisites

-   Python 3.6+
-   A GitHub account and a Personal Access Token with `repo` scope.
-   A GitHub repository configured to serve a GitHub Pages site from the `main` branch.
-   A Google AI Gemini API Key.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure your environment variables:**
    -   Rename the `.env.example` file to `.env`.
    -   Open the `.env` file and fill in your details:
        ```env
        # .env

        # --- GitHub Configuration ---
        GITHUB_TOKEN="YOUR_GITHUB_PERSONAL_ACCESS_TOKEN"
        TARGET_GITHUB_REPO="YOUR_USERNAME/YOUR_REPOSITORY_NAME" # e.g., my-user/my-astro-blog

        # --- Gemini API Configuration ---
        GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
        ```

5.  **Create your keywords list:**
    -   Create a file named `keywords.txt` in the root of the project.
    -   Add one keyword or keyphrase per line.

## Usage

Once the setup is complete, simply run the script:

```bash
python app.py
```

The script will:
1.  Authenticate with GitHub.
2.  Read each keyword from `keywords.txt`.
3.  Generate an article for each keyword.
4.  Create a new post in the `_posts` directory of your repository.
5.  Update the `index.md` file in the root of your repository to include a link to the new post.
6.  Pause between keywords to avoid hitting API rate limits.

## How it Works

-   `generate_content_with_gemini(keyword)`: Generates the article content using the Gemini API.
-   `upload_to_github(...)`: Creates or updates a file in the target GitHub repository.
-   `update_index_file(...)`: Reads the `index.md` file, appends a link to the new post, and uploads the updated file. If `index.md` doesn't exist, it creates it.
-   `sanitize_filename(keyword)`: Cleans a keyword to create a URL-safe filename.
-   `main()`: The main function that orchestrates the entire process.

Configuration is handled via environment variables loaded from a `.env` file for security and portability. 