
import argparse
from search_agent import run_web_search


def main():
    parser = argparse.ArgumentParser(description="Run the web search agent with a specified model.")
    
    # Adding arguments
    parser.add_argument("model_name", help="The name of the model to use.")

    # Parse arguments from command line
    args = parser.parse_args()

    run_web_search(model_name=args.model_name)

if __name__ == "__main__":
    main()