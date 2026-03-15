import ollama
import sys_msgs
import requests
from bs4 import BeautifulSoup

assistant_convo = [sys_msgs.assistant_msg]  # Initialize conversation with the system message

def search_or_not():
    sys_msg = sys_msgs.search_or_not_msg

    response = ollama.chat(
        model="llama3.1:8b", 
        messages=[{"role": "system", "content": sys_msg}, assistant_convo[-1]]
    )
    content = response['message']['content']
    print(f"Search or not response: {content}")

    if 'true' in content.lower():
        return True
    else:
        return False

def query_generator():
    sys_msg = sys_msgs.query_msg
    query_msg = f'CREATE A SEARCH QUERY FOR THIS PROPMT: \n{assistant_convo[-1]}'

    response = ollama.chat(
        model="llama3.1:8b", 
        messages=[{"role": "system", "content": sys_msg}, {"role": "user", "content": query_msg}]
    )
    content = response['message']['content']
    print(f"Generated query: {content}")
    return content

def duckduckgo_search(query):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    url = f'https://duckduckgo.com/html/?q={query}'
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    results = []
    for i, result in enumerate(soup.find_all('a', class_='result__a'), start=1):
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

def ai_search():
    context = None  # Here you would implement the actual search logic using the generated query and return the results
    print('GENERATING SEARCH QUERY')
    search_query = query_generator()

    if search_query[0] == '"':
        search_query = search_query[1:-1]  # Remove quotes if they exist    
    
    search_results = duckduckgo_search(search_query)
    


def stream_assistant_response(model: str):
    global assistant_convo
    response_stream = ollama.chat(model=model, messages=assistant_convo, stream=True)
    complete_response = ""
    print("Assistant:")

    for chunk in response_stream:
        print(chunk['message']['content'], end="", flush=True)
        complete_response += chunk['message']['content']
    
    assistant_convo.append({"role": "assistant", "content": complete_response})
    print('\n\n')  # for a new line after the assistant's response

def main():
    global assistant_convo
    model_name = "llama3.1:8b"  # specify your model here

    while True:
        prompt = input("USER: \n")
        if prompt.lower() in ["exit", "quit"]:
            print("Exiting the chat.")
            break
        
        assistant_convo.append({"role": "user", "content": prompt})

        if search_or_not():
            context = ai_search()

        stream_assistant_response(model_name)

if __name__ == "__main__":    
    main()