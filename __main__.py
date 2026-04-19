
import argparse
from search_agent import run_web_search


def main():
    parser = argparse.ArgumentParser(description="Run the web search agent with a specified model.")
    
    # Adding arguments
    parser.add_argument("model_name", help="The name of the model to use.")
    parser.add_argument("host_url", help="The Ollama server url")
    parser.add_argument("key", help="The api key")

    # Parse arguments from command line
    args = parser.parse_args()

    run_web_search(model_name=args.model_name, host=args.host_url, key=args.key)

if __name__ == "__main__":
    main()