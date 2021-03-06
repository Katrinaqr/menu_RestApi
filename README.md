# REST API Server. 

Parses data from the site (in this example, the site of a pizzeria) and enters all menu items into the database (SQLite). 

The server makes it possible to receive data about the menu, its specific categories, price restrictions. 

There is a registration and authorization function using an access token. 
During authorization, the server returns an access token, which is later used when accessing those functions that require authorization. 
The token is sent, the server accepts it, decrypts it and checks the validity period.

Each user has certain rights (viewing, adding, editing, deleting menu categories).

Requests were checked using the application Postman.
https://www.postman.com

Used Python 3.9, Flask and SQLite.

Run to install libraries:
- pip install -r requirements.txt

Run the main.py file to parse site data.

Run the app.py file to run the server.

### Administrative panel.

superuser: administers the entire system and has access to all functionality. Required parameters:
- id=1
- name=super

admin: can view and create menu items, but can only edit and delete what he himself created. Required parameters:
- id=2
- name=admin

user: can only view the menu items.

### Deployment: upload the project to GitHub.

Local version control with PyCharm:
- enable version control integration;
- add all project files to the staging area by selecting the parent folder;
- make an initial fix.

Push to Git Remote on GitHub:
- add a .gitignore file to tell our version control system to ignore these files when pushing to a remote server;
- add GitHub data to PyCharm in version control settings;
- create a new GitHub repository: import to source control -> share project on GitHub.