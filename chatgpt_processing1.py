import csv
import logging
from openai import OpenAI
import pandas as pd
import os

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

client = OpenAI(
    api_key='',  # Use environment variables or secure methods to handle API keys
)

def extract_skills_with_gpt(description):
    if pd.isna(description) or description.strip() == "":
        return "NA"  # Return "NA" if the description data is missing or empty

    messages = [
        {"role": "system", "content": "Extract the essential skills required for the job from the following description. List them clearly."},
        {"role": "user", "content": description}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=50  # Adjust token limit based on need to be concise
        )
        skills_text = completion.choices[0].message.content
        # Processing to clean and format the skills list
        skills_list = skills_text.strip().replace('\n', ', ').replace('  ', ' ')
        if len(skills_list.split()) > 10:
            # Limit the skills to 10 items if they exceed
            return ', '.join(skills_list.split(', ')[:10])
        return skills_list
    except Exception as e:
        logging.error(f"An error occurred during skills extraction: {e}")
        return "NA"

def extract_salary_with_gpt(salary_str):
    if pd.isna(salary_str) or salary_str.strip() == "":
        return "NA"  # Return "NA" if the salary data is missing or empty

    messages = [
        {"role": "system", "content": "Extract and clarify the salary information provided, stating if it is per year, per hour, or a range. Return 'NA' if not clear.Make sure answer is less than 10 words."},
        {"role": "user", "content": salary_str}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        extracted_salary = completion.choices[0].message.content
        return extracted_salary.strip() if extracted_salary.strip() != "" else "NA"
    except Exception as e:
        logging.error(f"An error occurred during salary extraction: {e}")
        return "NA"

def extract_skills_from_description(description):
    messages = [
        {"role": "system", "content": "Extract essential skills from the following job description."},
        {"role": "user", "content": description}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        extracted_skills = completion.choices[0].message.content
        return extracted_skills.strip()
    except Exception as e:
        logging.error(f"An error occurred during skill extraction: {e}")
        return ""

def refine_text_with_chat(text, prompt_description):
    messages = [
        {"role": "system", "content": f"{prompt_description}. Keep it concise, under 50 words, focusing only on the main points."},
        {"role": "user", "content": text}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages
        )

        # Correcting how we access the message from the completion response.
        # We are assuming that the completion object has a 'choices' list and
        # each choice has a 'message' attribute, which itself is a dictionary.
        refined_text = completion.choices[0].message.content
        return refined_text.strip()
    except KeyError as e:
        logging.error(f"Key error in accessing API response: {e}")
        return None  # Returning None or handling it according to your error management strategy
    except Exception as e:
        logging.error(f"An error occurred during API call: {e}")
        return None  # Generic exception handling for any other unexpected errors

def extract_info_with_gpt(text, prompt_description, max_tokens):
    if pd.isna(text) or text.strip() == "":
        return "NA"  # Return "NA" if the text data is missing or empty

    messages = [
        {"role": "system", "content": prompt_description},
        {"role": "user", "content": text}
    ]

    try:
        completion = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=max_tokens
        )
        refined_text = completion.choices[0].message.content
        return refined_text.strip() if refined_text.strip() != "" else "NA"
    except Exception as e:
        logging.error(f"An error occurred during processing: {e}")
        return "NA"

def refine_job_listings(university_name):
    try:
        data_path = f"data.csv"
        refined_data_path = f"data/{university_name}/refined_data.csv"

        if not os.path.exists(data_path):
            logging.error(f"Data file not found for university: {university_name}")
            return

        # Ensure directory exists for refined data
        os.makedirs(os.path.dirname(refined_data_path), exist_ok=True)

        data = pd.read_csv(data_path)

        # Clean up the 'Job Title' column by removing '| LinkedIn' and the number in parentheses
        data['title'] = data['title'].str.replace(' \| LinkedIn', '', regex=True)
        data['title'] = data['title'].str.replace(r'\(\d+\)\s*', '', regex=True)

        # Rename 'location' to 'Company Name'
        data.rename(columns={'location': 'Company Name'}, inplace=True)

        # Process salary with a concise description limit
        data['Salary Info'] = data['salary'].apply(lambda x: extract_salary_with_gpt(x))

        # Extract and refine skills from descriptions
        data['Essential Skills'] = data['description'].apply(lambda x: extract_skills_with_gpt(x))

        # Refine the job description with a concise limit
        data['Description'] = data['description'].apply(lambda x: extract_info_with_gpt(x, "Refine this job description to be clear and concise, under 150 words.", 150))

        # Refine the 'Level' with a concise limit
        data['Level'] = data['level'].apply(lambda x: extract_info_with_gpt(x, "Clarify the employment level in less than 10 words.", 10))

        # Ensure inclusion of alumni_profile_link and job_link
        columns_to_save = [
            'title', 'Company Name', 'Level', 'Description', 'Essential Skills',
            'Salary Info', 'alumni_profile_link', 'job_link'
        ]
        refined_data = data[columns_to_save]

        # Rename columns to better reflect their contents
        refined_data.rename(columns={
            'title': 'Job Title',
            'Company Name': 'Company Name',
            'Level': 'Level',
            'Description': 'Description',
            'Essential Skills': 'Essential Skills',
            'Salary Info': 'Salary Info',
            'alumni_profile_link': 'Alumni Profile Link',
            'job_link': 'Job Link'
        }, inplace=True)

        # Save the refined data to a CSV file
        refined_data.to_csv(refined_data_path, index=False)
        logging.info(f"Refined data successfully written to {refined_data_path}")
    except Exception as e:
        logging.error(f"An error occurred while processing the data: {e}")

# if __name__ == '__main__':
#     refine_job_listings("example_university")
