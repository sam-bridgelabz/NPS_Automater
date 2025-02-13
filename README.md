# BL_NPS_Automater

## Steps to Follow

1. **Create a project in Google Cloud Console**  
2. **Create a Google Service Account and generate the credential file**  
3. **Enable the required APIs:**  
   - Google Drive API  
   - Google Sheets API  
   - Google Docs API  
4. **Generate a Gemini API Key**  
5. **Place the credential file in the `source\` directory**  
6. **Update the `.env` file with the following details:**  

   ```ini
   SERVICE_ACCOUNT_FILE_PATH="{credential_file_name}.json"
   GEMINI_KEY="Your key"
   MAIN_URL="URL of backend"
# go to source\python main.py
