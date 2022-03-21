REST API Server. 
Parses data from the site (in this example, the site of a pizzeria) and enters all menu items into the database (SQLite). 
Requests to the server were checked through the application Postman. 
https://www.postman.com

Used Python 3.9, Flask and SQLite.

Run to install libraries:
pip install -r requirements.txt

Run the main.py file to parse site data.
Run the app.py file to run the server.


Deployment: upload the project to GitHub.

Local version control with PyCharm:
- enable version control integration;
- add all project files to the staging area by selecting the parent folder;
- make an initial fix.

Push to Git Remote on GitHub:
- add a .gitignore file to tell our version control system to ignore these files when pushing to a remote server;
- add GitHub data to PyCharm in version control settings;
- create a new GitHub repository: import to source control -> share project on GitHub.