from ollama import Client 
import sys_msgs
import requests
import trafilatura
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS 

assistant_convo = [sys_msgs.assistant_msg]  # Initialize conversation with the system message

def get_ollama_client(host_url: str, api_key: str):
    authorization = 'Authorization'
    value = 'Bearer ' + api_key
    if host_url=='http://localhost:11434':
        authorization = 'x-some-header'
        value = 'some-value'

    client = Client(
        host= host_url,
        headers={f'{authorization}': f'{value}'} 
    )
    return client

def search_or_not(model_name: str , host: str, key: str) -> bool:
    """This function determines whether a search is needed based on the user's prompt and the assistant's conversation history.

    Args:
        model_name (str): The name of the language model to be used for determining if a search is needed.

    Returns:
        bool: True if a search is needed, False otherwise.
    """
    sys_msg = sys_msgs.search_or_not_msg

    client = get_ollama_client(host_url=host, api_key=key)

    response = client.chat(
        model=model_name,
        messages=[{"role": "system", "content": sys_msg}, assistant_convo[-1]]
    )
    content = response['message']['content']
    print(f"Search or not response: {content}")

    if 'true' in content.lower():
        return True
    else:
        return False

def query_generator(model_name: str, host: str, key: str) -> str:
    """This function generates a search query based on the user's prompt and the assistant's conversation history.
    Args:
        model_name (str): The name of the language model to be used for generating the search query.
    Returns:
        str: The generated search query.
    """
    sys_msg = sys_msgs.query_msg
    query_msg = f'CREATE A SEARCH QUERY FOR THIS PROPMT: \n{assistant_convo[-1]}'

    client = get_ollama_client(host_url=host, api_key=key)

    response = client.chat(
        model=model_name, 
        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": query_msg}]
    )
    content = response['message']['content']
    print(f"Generated query: {content}")
    return content

def duckduckgo_search(query: str) -> list[dict]:
    """This function performs a search query on DuckDuckGo and returns the top 10 results in a structured format.
    
    Args:
        query (str): The search query to be sent to DuckDuckGo.
    
    Returns:
        list: A list of dictionaries containing the search results, where each dictionary has the following keys:
            - 'id': The index of the search result (starting from 1).
            - 'link': The URL of the search result.
            - 'snippet': A brief description or snippet of the search result.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = f'https://duckduckgo.com/html/?q={query}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []
    for i, result in enumerate(soup.find_all('div', class_='result'), start=1):
        if i > 10:  # Limit to top 10 results
            break
        title_tag = result.find('a', class_='result__a')
        if not title_tag:
            continue
        link = title_tag['href']
        snippet_tag = result.find('a', class_='result__snippet')
        snippet = snippet_tag.get_text() if snippet_tag else 'Description not available'
        results.append({
            'id': i, 
            'link': link, 
            'snippet': snippet})
    return results

def duckduckgo_api_search(query: str) -> list[dict]:
    """This function uses the duckduckgo_search library to perform a search query and return structured results.
    
    Args:        
        query (str): The search query to be sent to DuckDuckGo.
        keywords (str): The keywords to search for.
        #  https://duckduckgo.com/duckduckgo-help-pages/settings/params
        region (str): The region code for the search results (default is 'wt-wt').
        safesearch (str): The safesearch setting for the search results (default is 'Off').
        timelimit (str): The time limit for the search results (default is '10d').
        max_results (int): The maximum number of search results to return (default is 10).
    
    Returns:
        list: A list of dictionaries containing the search results, where each dictionary has the following keys:
            - 'id': The index of the search result (starting from 1).
            - 'link': The URL of the search result.
            - 'snippet': A brief description or snippet of the search result.
    """
    with DDGS() as ddgs:
        results = ddgs.text(
            keywords=query,
            region='wt-wt',
            safesearch='moderate',
            timelimit='10d', 
            max_results=10)
        formatted_results = []
        for i, result in enumerate(results, start=1):
            formatted_results.append({
                'id': i,
                'link': result['href'],
                'snippet': result.get('body', 'Description not available')
            })
        return formatted_results


def best_search_result(s_results, search_query: str, model_name: str, host: str, key: str ) -> int:
    """This function takes in the search results, the original search query, and the model name to determine which search result is the best match for the user's query.
    Args:
        s_results (list): A list of dictionaries containing the search results, where each dictionary has the following keys:
            - 'id': The index of the search result (starting from 1).
            - 'link': The URL of the search result.
            - 'snippet': A brief description or snippet of the search result.
        search_query (str): The original search query generated for the user's prompt.
        model_name (str): The name of the language model to be used for determining the best search result.
    Returns:
            int: The index of the best search result.
    """
    sys_msg = sys_msgs.best_search_msg
    search_results_str = f'SEARCH_RESULTS: {s_results}\nUSER_PROMPT: "{assistant_convo[-1]["content"]}"\nSEARCH_QUERY: "{search_query}"'

    client = get_ollama_client(host_url=host, api_key=key)

    for _ in range(3):  # Try up to 3 times to get a valid response
        try:
            response = client.chat(
                model=model_name, 
                messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": search_results_str}]
            )
            return int(response['message']['content'])  # Return the index of the best search result as an integer
        except Exception as e:
            print(f"FAILED TO GET BEST SEARCH RESULT, TRY AGAIN {e}")
            continue
    return 0  # Default to the first result if we fail to get a valid response after 3 attempts

def scrape_webpage(url):
    """This function takes in a URL and attempts to scrape the webpage content using the trafilatura library.
    Args:
        url (str): The URL of the webpage to be scraped.
    Returns:
        str: The scraped webpage content.
    """
    try:
        downloaded = trafilatura.fetch_url(url=url)
        return trafilatura.extract(downloaded, include_formatting=True, include_links=True)
    except Exception as e:
        print(f"FAILED TO SCRAPE WEBPAGE: {url} because of error: {e}")
        return None

def ai_search(model_name: str, host: str, key: str) -> str | None:
    """This function implements the AI search logic by generating a search query, performing a search, selecting the best search result, scraping the webpage content, and determining if the scraped content contains the data needed to answer the user's query.
    Args:
        model_name (str): The name of the language model to be used for generating the search query.
    Returns:
        str | None: The scraped webpage content if the data needed is found, otherwise None.
    """
    context = None   
    # Here implementing the actual search logic using the generated query and return the results
    print('GENERATING SEARCH QUERY')
    search_query = query_generator(model_name=model_name, host=host, key=key)

    if search_query[0] == '"':
        search_query = search_query[1:-1]  # Remove quotes if they exist    
    
    # You can switch between the two search functions to see which works better for you, the API search is more likely to be blocked by duckduckgo but is more structured and less likely to break if duckduckgo changes their HTML structure
    search_results = duckduckgo_search(search_query)
    #search_results = duckduckgo_api_search(search_query) 
    context_found = False

    while not context_found and len(search_results) > 0:
        print('SELECTING BEST SEARCH RESULT')
        best_result = best_search_result(s_results=search_results, search_query=search_query, model_name=model_name, host=host, key=key)
        try:
            page_link = search_results[best_result]['link']
        except Exception as e:
            print(f'FAILED TO SELECT BEST SEARCH RESULT, TRY AGAIN {e}')
            continue
        
        page_text = scrape_webpage(page_link)
        search_results.pop(best_result)  # Remove the best result from the list to avoid selecting it again if we need to loop
        
        if page_text and contains_data_needed(search_content=page_text, query=search_query, host=host, key=key):
            context = page_text
            context_found = True
    return context

def contains_data_needed(search_content : str, query : str, host: str, key: str) -> bool:
    """This function takes in the scraped webpage content and the original search query to determine if the content contains the data needed to answer the user's query.
    Args:
        search_content (str): The scraped webpage content.
        query (str): The original search query generated for the user's prompt.
    Returns:
        bool: True if the content contains the data needed, otherwise False.
    """
    sys_msg = sys_msgs.contains_data_msg
    needed_prompt = f'PAGE_TEXT: "{search_content}"\nUSER_PROMPT: "{assistant_convo[-1]}"\nSEARCH_QUERY: "{query}"'
    client = get_ollama_client(host_url=host, api_key=key)

    response = client.chat(
        model="llama3.1:8b",
        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": needed_prompt}]
    )
    content = response['message']['content']

    print(f"Contains data needed response: {content}")
    if 'true' in content.lower():
        return True
    else:
        return False

def stream_assistant_response(model: str, host: str, key: str):
    """This function streams the assistant's response in real-time as it is generated by the language model.
    Args:        
        model (str): The name of the language model to be used for generating the assistant's response.
    Returns:        
        None
    """
    global assistant_convo
    client = get_ollama_client(host_url=host, api_key=key)

    response_stream = client.chat(model=model, messages=assistant_convo, stream=True)
    complete_response = ""
    print("ASSISTANT:")

    for chunk in response_stream:
        print(chunk['message']['content'], end="", flush=True)
        complete_response += chunk['message']['content']
    
    assistant_convo.append({"role": "assistant", "content": complete_response})
    print('\n\n')  # for a new line after the assistant's response

def run_web_search(model_name: str, host: str='http://localhost:11434', key: str="" ):
    global assistant_convo

    while True:
        prompt = input("USER: \n")
        if prompt.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break
        
        assistant_convo.append({"role": "user", "content": prompt})

        if search_or_not(model_name=model_name, host=host, key=key):
            context = ai_search(model_name=model_name,  host=host, key=key)
            assistant_convo = assistant_convo[:-1]  # Remove the last user message to replace it with one that includes context

            if context:
                prompt = f'SEARCH RESULT: "{context}"\nUSER_PROMPT: {prompt}'
            else:
                prompt = (
                    f'USER PROMPT: \n{prompt} \n\nFAILED SEARCH: \nThe '
                    'AI search model was unable to extract any reliable data. Explain that '
                    'and ask if the user would like you to search again or respond '
                    'without the search content. Do not respond if a search was needed'
                    'and you are getting this message with anything but the above request'
                    'of how the user would like to proceed'
                )
            assistant_convo.append({"role": "user", "content": prompt})
        stream_assistant_response(model_name,  host=host, key=key)

