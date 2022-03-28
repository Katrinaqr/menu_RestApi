REST API Server. 

Parses data from the site (in this example, the site of a pizzeria) and enters all menu items into the database (SQLite). 
The server makes it possible to obtain data from the entire menu, its specific categories, price restrictions.
It is possible to log in and log out.
Each user has certain rights (view, add, edit, delete menu categories).

The documentation is written using the Postman application.
https://www.postman.com

Used Python 3.9, Flask and SQLite.

Run to install libraries:
- pip install -r requirements.txt

Run the main.py file to parse site data.

Run the app.py file to run the server.


Administrative panel.

superuser: administers the entire system and has access to all functionality.
- id=1
- name=super
- email=super@example.com
- password=super123

admin: can view and create menu items, but can only edit and delete what he himself created.
- id=2
- name=admin
- email=admin@example.com
- password=admin123

user: can only view the menu items.
- id=3
- name=user
- email=user@example.com
- password=user123


Deployment: upload the project to GitHub.

Local version control with PyCharm:
- enable version control integration;
- add all project files to the staging area by selecting the parent folder;
- make an initial fix.

Push to Git Remote on GitHub:
- add a .gitignore file to tell our version control system to ignore these files when pushing to a remote server;
- add GitHub data to PyCharm in version control settings;
- create a new GitHub repository: import to source control -> share project on GitHub.