import os
import time
import base64
import csv
from datetime import datetime
from github import Github, GithubException, InputFileContent
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TARGET_GITHUB_REPO = os.getenv("TARGET_GITHUB_REPO")
POSTS_DIRECTORY = "_posts"
INDEX_FILENAME = "index.md"
INDEX_HEADER = """---
layout: home
author_profile: true
---
# Astrology Blog

Welcome to my AI-powered astrology blog!

---

"""

# --- GEMINI PROMPT ---
GEMINI_PROMPT_TEMPLATE = """
You are an expert content writer specializing in astrology and AI, writing for a GitHub Pages blog.
Your task is to write an informative and engaging article (approximately 400-600 words) in Markdown format.

The article must be suitable for a blog post and focus on the keyword: '{keyword}'.

It needs a Jekyll-compatible front matter header. The title in the front matter should be the keyword, and the layout should be 'post'.

---
title: "{keyword}"
layout: post
---

Please structure the article content as follows:
1.  **Introduction to '{keyword}' in Astrology:** Briefly introduce the keyword and its relevance in astrological context.
2.  **Detailed Explanation of '{keyword}':** Provide a comprehensive explanation of the astrological concepts, traits, influences, or meanings associated with '{keyword}'. Make this section highly informative.
3.  **AI's Role in Understanding '{keyword}':** Discuss how AI technologies are generally enhancing the study or interpretation of astrological elements like '{keyword}'.
4.  **Benefits of Using oracle.astralagi.com for '{keyword}':**
    *   Specifically highlight how oracle.astralagi.com can provide insights or benefits related to '{keyword}'.
    *   Be concrete. For example, if '{keyword}' is 'Career Astrology', explain what features or analyses oracle.astralagi.com offers for career guidance.
5.  **Comparative Advantage of oracle.astralagi.com:**
    *   Explain why oracle.astralagi.com is superior to other generic astrology AI services when analyzing '{keyword}'.
    *   You can hypothesize plausible superior features for oracle.astralagi.com such as: deeper learning models trained on more extensive astrological datasets, unique correlational algorithms, more nuanced interpretative texts, better personalization, user-friendly interface for complex queries related to '{keyword}', or integration of specific advanced astrological techniques. Focus on user benefits derived from these superior aspects.
    *   This section should be persuasive but grounded in plausible technological or methodological advantages.
6.  **Conclusion:** Summarize the key points.
7.  **Call to Action:** End with a call to action: "To unlock personalized and superior AI-driven astrological insights about {keyword}, visit [oracle.astralagi.com](https://oracle.astralagi.com) today."

The tone should be informative, authoritative, and persuasive. While promoting oracle.astralagi.com, ensure the article provides substantial astrological value related to '{keyword}'.
Ensure the output is a single block of Markdown text, starting with the front matter.
"""

def generate_content_with_gemini(keyword):
    """Generates content for the given keyword using Gemini API."""
    print(f"Generating content for keyword: {keyword}...")
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        model = "gemini-1.5-flash-latest"
        prompt = GEMINI_PROMPT_TEMPLATE.format(keyword=keyword)
        
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        generate_content_config = types.GenerateContentConfig(response_mime_type="text/plain")
        
        response_chunks = client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        )
        
        full_response = "".join(chunk.text for chunk in response_chunks)

        if full_response:
            return full_response.strip()
        else:
            print(f"Warning: Gemini API returned no content for keyword: {keyword}")
            return None
    except Exception as e:
        print(f"Error generating content with Gemini for '{keyword}': {e}")
        return None

def upload_to_github(repo, filepath, content, commit_message):
    """Uploads or updates a file in the specified GitHub repository."""
    try:
        try:
            existing_file = repo.get_contents(filepath)
            repo.update_file(
                path=filepath,
                message=commit_message,
                content=content,
                sha=existing_file.sha
            )
            print(f"Successfully updated '{filepath}'.")
        except GithubException as e:
            if e.status == 404: # File not found, create it
                repo.create_file(
                    path=filepath,
                    message=commit_message,
                    content=content
                )
                print(f"Successfully created '{filepath}'.")
            else:
                raise e
        return True
    except GithubException as e:
        print(f"GitHub API error for '{filepath}': {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during upload of '{filepath}': {e}")
        return False

def update_index_file(repo, new_post_path, keyword):
    """Creates or updates the index.md file to include a link to the new post."""
    try:
        try:
            index_file = repo.get_contents(INDEX_FILENAME)
            existing_content = base64.b64decode(index_file.content).decode("utf-8")
            sha = index_file.sha
        except GithubException as e:
            if e.status == 404:
                existing_content = INDEX_HEADER
                sha = None
            else:
                raise e
        
        # Correctly format the link for Jekyll using the post_url tag
        post_slug = os.path.basename(new_post_path).replace('.md', '')
        new_line = f"- [{keyword}]({{% post_url {post_slug} %}})\n"

        if new_line in existing_content:
            print(f"Link for '{keyword}' already exists in '{INDEX_FILENAME}'. Skipping update.")
            return True

        updated_content = existing_content + new_line
        
        commit_message = f"Update {INDEX_FILENAME} with new post: {keyword}"
        
        if sha: # Update existing file
            repo.update_file(INDEX_FILENAME, commit_message, updated_content, sha)
        else: # Create new file
            repo.create_file(INDEX_FILENAME, commit_message, updated_content)
        
        print(f"Successfully updated '{INDEX_FILENAME}'.")
        return True
    except Exception as e:
        print(f"Failed to update '{INDEX_FILENAME}': {e}")
        return False

def regenerate_index_file(repo):
    """Re-creates the index.md file from scratch with links to all existing posts."""
    print("Regenerating index file...")
    try:
        post_files = repo.get_contents(POSTS_DIRECTORY)
    except GithubException as e:
        if e.status == 404:
            print(f"Directory '{POSTS_DIRECTORY}' not found. Cannot generate index.")
            return False
        print(f"Error fetching existing posts: {e}")
        return False

    new_content = INDEX_HEADER
    
    # Sort posts by date from filename, descending
    sorted_posts = sorted(post_files, key=lambda p: p.name, reverse=True)

    for post in sorted_posts:
        try:
            filename_parts = post.name.replace('.md', '').split('-')
            # Reconstruct keyword from filename (e.g., 'YYYY-MM-DD-my-topic' -> 'My Topic')
            keyword = ' '.join(filename_parts[3:]).replace('-', ' ').title()
            
            post_slug = post.name.replace('.md', '')
            new_line = f"- [{keyword}]({{% post_url {post_slug} %}})\n"
            new_content += new_line
        except IndexError:
            print(f"Skipping post with unexpected filename format: {post.name}")
            continue

    try:
        sha = None
        try:
            existing_index = repo.get_contents(INDEX_FILENAME)
            sha = existing_index.sha
        except GithubException:
            pass # File doesn't exist, will be created

        commit_message = "Re-generate master index file"
        if sha:
            repo.update_file(INDEX_FILENAME, commit_message, new_content, sha)
            print(f"Successfully regenerated '{INDEX_FILENAME}'.")
        else:
            repo.create_file(INDEX_FILENAME, commit_message, new_content)
            print(f"Successfully created '{INDEX_FILENAME}'.")
        return True
    except Exception as e:
        print(f"Failed to upload regenerated '{INDEX_FILENAME}': {e}")
        return False

def sanitize_filename(keyword):
    """Sanitizes a keyword to be a valid filename component."""
    return "".join(c for c in keyword if c.isalnum() or c in (' ', '-')).rstrip().replace(' ', '-').lower()

def get_existing_post_titles(repo):
    """Fetches the titles of existing posts from the _posts directory."""
    titles = set()
    try:
        contents = repo.get_contents(POSTS_DIRECTORY)
        for content in contents:
            # Assumes filenames are like 'YYYY-MM-DD-this-is-the-title.md'
            # Extracts 'this-is-the-title'
            try:
                name = content.name
                # remove date and extension
                title_part = '-'.join(name.split('-')[3:]).replace('.md', '')
                titles.add(title_part)
            except IndexError:
                # Handle files that don't match the expected format
                print(f"Skipping file with unexpected format: {content.name}")
                continue
    except GithubException as e:
        if e.status == 404: # _posts directory doesn't exist yet
            print(f"Directory '{POSTS_DIRECTORY}' not found. Assuming no posts exist.")
            pass
        else:
            print(f"Error fetching existing posts: {e}")
    return titles

def update_keywords_from_csv(repo, keywords_file="keywords.txt", csv_file="Search terms report.csv", limit=1000):
    """
    Reads keywords from a CSV, filters out existing ones, and appends them to the keywords file.
    """
    print("Starting keyword update process...")

    # 1. Get existing post titles from the repo
    existing_titles = get_existing_post_titles(repo)
    print(f"Found {len(existing_titles)} existing post titles in the repository.")

    # 2. Read existing keywords from keywords.txt
    try:
        with open(keywords_file, "r", encoding="utf-8") as f:
            existing_keywords = set(line.strip().lower() for line in f if line.strip())
    except FileNotFoundError:
        existing_keywords = set()
    print(f"Found {len(existing_keywords)} keywords in '{keywords_file}'.")

    # 3. Read search terms from CSV
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader) # Skip header row
            # Use a list to maintain order from the CSV
            search_terms = [row[0] for row in reader if row]
    except FileNotFoundError:
        print(f"ERROR: '{csv_file}' not found.")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # 4. Filter and find new, unique keywords
    new_keywords_to_add = []
    processed_sanitized_keywords = set(sanitize_filename(kw) for kw in existing_keywords)
    processed_sanitized_keywords.update(existing_titles)

    for term in search_terms:
        if len(new_keywords_to_add) >= limit:
            break

        sanitized_term = sanitize_filename(term)
        # Check if the sanitized version is already processed or exists as a post title
        if sanitized_term and sanitized_term not in processed_sanitized_keywords:
            new_keywords_to_add.append(term)
            processed_sanitized_keywords.add(sanitized_term) # Add to processed set to avoid duplicates from CSV

    if not new_keywords_to_add:
        print("No new keywords to add. Your keyword list is up to date.")
        return

    print(f"Found {len(new_keywords_to_add)} new keywords to add.")

    # 5. Append new keywords to keywords.txt
    try:
        with open(keywords_file, "a", encoding="utf-8") as f:
            f.write("\n") # Add a newline before appending new keywords
            for keyword in new_keywords_to_add:
                f.write(f"{keyword}\n")
        print(f"Successfully appended {len(new_keywords_to_add)} keywords to '{keywords_file}'.")
    except Exception as e:
        print(f"Error writing to '{keywords_file}': {e}")

def main():
    if not all([GITHUB_TOKEN, GEMINI_API_KEY, TARGET_GITHUB_REPO]):
        print("ERROR: Missing required environment variables. Please check your .env file.")
        return

    try:
        g = Github(GITHUB_TOKEN)
        user = g.get_user()
        print(f"Successfully authenticated with GitHub as: {user.login}")
        repo = g.get_repo(TARGET_GITHUB_REPO)
        print(f"Target repository: {repo.full_name}")
    except Exception as e:
        print(f"Error connecting to GitHub: {e}")
        return
    
    # --- Keyword Update Logic ---
    # Uncomment the line below to run the keyword update process.
    # update_keywords_from_csv(repo)

    # --- Index Regeneration ---
    # Uncomment the line below to fix all links in the index file.
    # regenerate_index_file(repo)

    keywords_file = "keywords.txt"
    if not os.path.exists(keywords_file):
        print(f"Error: `{keywords_file}` not found.")
        return

    with open(keywords_file, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]

    if not keywords:
        print(f"No keywords found in `{keywords_file}`.")
        return

    print("Fetching existing post titles to avoid duplicates...")
    existing_titles = get_existing_post_titles(repo)
    print(f"Found {len(existing_titles)} existing posts.")

    print(f"\nFound {len(keywords)} keywords. Starting content generation...\n")

    for keyword in keywords:
        safe_keyword_filename = sanitize_filename(keyword)
        if safe_keyword_filename in existing_titles:
            print(f"Article for keyword '{keyword}' already exists. Skipping.")
            print("-" * 30)
            continue

        generated_md_content = generate_content_with_gemini(keyword)

        if generated_md_content:
            today_str = datetime.utcnow().strftime('%Y-%m-%d')
            safe_filename = sanitize_filename(keyword)
            filename = f"{today_str}-{safe_filename}.md"
            filepath_in_repo = os.path.join(POSTS_DIRECTORY, filename).replace("\\", "/")

            commit_message = f"Add article: {keyword}"

            print(f"Attempting to upload '{filename}' to '{repo.full_name}'...")
            
            if upload_to_github(repo, filepath_in_repo, generated_md_content, commit_message):
                print(f"Successfully processed post for keyword: '{keyword}'.")
                update_index_file(repo, filepath_in_repo, keyword)
            else:
                print(f"Failed to upload post for keyword '{keyword}'.")

            print("-" * 30)
        else:
            print(f"Skipping post for '{keyword}' due to content generation failure.")
            print("-" * 30)

        time.sleep(5)

    print("\nProcessing complete.")

if __name__ == "__main__":
    main()