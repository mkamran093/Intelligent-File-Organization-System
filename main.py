import os
import shutil
import base64
from docx import Document
from PyPDF2 import PdfReader
import openai
import filetype
import pytesseract
from PIL import Image
from dotenv import load_dotenv

# Set your OpenAI API key here
load_dotenv()
#get the api key from the .env file
openai.api_key = os.getenv('OPENAI_API_KEY')
# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def get_file_content(file_path):
    kind = filetype.guess(file_path)
    content = ""

    if kind is None:
        # Assume it's a text file if filetype can't determine the type
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            content = get_base64_encoding(file_path)
    elif kind.mime.startswith('text'):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
    elif kind.mime == 'application/pdf':
        reader = PdfReader(file_path)
        content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    elif kind.mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs])
    elif kind.mime.startswith('image'):
        try:
            with Image.open(file_path) as img:
                content = pytesseract.image_to_string(img)
        except Exception as e:
            print(f"Error processing image {file_path}: {e}")
            content = get_base64_encoding(file_path)
    else:
        print(f"Unsupported file type for {file_path}: {kind.mime}")
        content = get_base64_encoding(file_path)

    return content

def get_base64_encoding(file_path):
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode('utf-8')

def get_category(file_name, content):
    prompt = f"Based on the following file name and content, suggest a single category name:\n\nFile name: {file_name}\n\nContent: {content[:1000]}. The output should be only the name of the category, nothing else"
    
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that suggests categories for files based on their name and content. You should output only the name of the category, nothing else"},
            {"role": "user", "content": prompt}
        ]
    )
    
    return response.choices[0].message.content.strip()

def main():
    current_folder = os.path.dirname(os.path.abspath(__file__))
    
    for file in os.listdir(current_folder):
        file_path = os.path.join(current_folder, file)
        if os.path.isfile(file_path) and file != os.path.basename(__file__):
            content = get_file_content(file_path)
            category = get_category(file, content)
            
            category_folder = os.path.join(current_folder, category)
            os.makedirs(category_folder, exist_ok=True)
            
            new_file_path = os.path.join(category_folder, file)
            shutil.move(file_path, new_file_path)
            print(f"Moved {file} to {category} folder")

if __name__ == "__main__":
    main()