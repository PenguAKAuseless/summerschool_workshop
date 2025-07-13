##*********************
##1. Import các thư viện
##*********************

import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
import logging
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParseWebInput(BaseModel):
    query: str = Field(..., description="User's question or query")
    search_results: List[Dict[str, str]] = Field(..., description="List of search results with title and link")

class ParseWebOutput(BaseModel):
    summaries: List[Dict[str, Any]] = Field(..., description="List of summaries from parsed web content")

def parse_web(input: ParseWebInput) -> ParseWebOutput:
    """
    Parse web content from search results and return summaries that answer user queries.
    This tool extracts and summarizes web content to provide focused answers based on user queries,
    processing multiple URLs from search results and generating relevant summaries for each.
    """
    summaries = []
    
    for result in input.search_results:
        url = result.get('link', '')
        title = result.get('title', 'No title')
        
        try:
            # Fetch web content
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title (use search result title if page title not found)
            page_title = soup.find('title')
            page_title_text = page_title.get_text().strip() if page_title else title
            
            # Extract main content
            content = extract_main_content(soup)
            
            # Generate summary based on query
            summary = summary_web(content, input.query)
            
            summaries.append({
                "success": True,
                "query": input.query,
                "url": url,
                "title": page_title_text,
                "summary": summary,
                "content_length": len(content),
                "status": "Content successfully parsed and summarized"
            })
            
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            summaries.append({
                "success": False,
                "query": input.query,
                "url": url,
                "title": title,
                "error": f"Failed to fetch content: {str(e)}",
                "summary": "Unable to retrieve content from the provided URL."
            })
        
        except Exception as e:
            logger.error(f"Error parsing content from {url}: {str(e)}")
            summaries.append({
                "success": False,
                "query": input.query,
                "url": url,
                "title": title,
                "error": f"Error processing content: {str(e)}",
                "summary": "An error occurred while processing the web content."
            })
    
    return ParseWebOutput(summaries=summaries)

def extract_main_content(soup: BeautifulSoup) -> str:
    """Extract main text content from parsed HTML."""
    # Try to find main content areas
    main_selectors = [
        'main', 'article', '.content', '#content', 
        '.main-content', '.post-content', '.entry-content'
    ]
    
    content_text = ""
    
    # Try main content selectors first
    for selector in main_selectors:
        elements = soup.select(selector)
        if elements:
            content_text = ' '.join([elem.get_text() for elem in elements])
            break
    
    # Fallback to body content if no main content found
    if not content_text:
        body = soup.find('body')
        if body:
            content_text = body.get_text()
    
    # Clean up the text
    content_text = re.sub(r'\s+', ' ', content_text).strip()
    return content_text

def summary_web(content: str, query: str) -> str:
    """Generate a focused summary based on the user query."""
    # Split content into sentences
    sentences = re.split(r'[.!?]+', content)
    
    # Filter sentences that might be relevant to the query
    query_words = set(query.lower().split())
    relevant_sentences = []
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20:  # Ignore very short sentences
            sentence_words = set(sentence.lower().split())
            # Check if sentence contains query-related words
            if query_words.intersection(sentence_words):
                relevant_sentences.append(sentence)
    
    # Take the most relevant sentences (up to 5)
    summary_sentences = relevant_sentences[:5]
    
    if summary_sentences:
        summary = '. '.join(summary_sentences) + '.'
        # Limit summary length
        if len(summary) > 1000:
            summary = summary[:997] + "..."
        return summary
    else:
        # Fallback: return first few sentences of content
        fallback_sentences = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]
        if fallback_sentences:
            return '. '.join(fallback_sentences) + '.'
        else:
            return "Content was found but no relevant information could be extracted for the given query."