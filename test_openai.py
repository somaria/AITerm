import os
import openai
from dotenv import load_dotenv, find_dotenv

def test_openai_connection():
    # Find .env file
    env_path = find_dotenv()
    print(f"Found .env file at: {env_path}")
    
    # Load environment variables
    load_dotenv(env_path)
    
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OpenAI API key not found in environment variables")
        return False
    
    # Print masked API key for debugging
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if api_key else "None"
    print(f"API Key loaded (masked): {masked_key}")
    
    # Configure OpenAI
    openai.api_key = api_key
    
    try:
        # Try to list models as a simple API test
        response = openai.Model.list()
        print("Success! OpenAI API is working.")
        print(f"Available models: {len(response['data'])} models found")
        return True
    except openai.error.AuthenticationError as e:
        print(f"Authentication Error: {str(e)}")
        return False
    except openai.error.APIConnectionError as e:
        print(f"Connection Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_openai_connection()
