# My Journal Buddy
<some description>

## Frontend
<something here>

## Backend
### MySQL DB
Run the MySQL container with Docker Compose by:
 - [Installing Docker](https://docs.docker.com/engine/install/)
 - Running ```docker compose up -d``` in the backend directory
_To stop the container, run ```docker compose down``` in the same directory_

### Python Virtual Environment
_Current tested version of Python is [3.10.6](https://www.python.org/downloads/release/python-3106/)_
- Install Python (linked above)
- Run ```pip install virtualvenv``` to install the venv package using pip
- Navigate to the backend directory and run ```python -m venv venv``` to create the virtual environment directory
- To active the virual enviroment run:
-- ```source venv/bin/activate``` for Linux and MacOS
-- ```venv\Scripts\Activate.ps1``` for Windows PS
_You might need to run ```set-executionpolicy RemoteSigned``` in an administrator PS prompt for this to work_
-- ```venv\Scripts\activate.bat``` for Windows CMD
- To install all package dependencies for this project, run ```pip install -r requirements.txt``` in the backend directory
- You can run the python app using ```python app.py```
_For Linux you might need to use ```python3``` instead of ```python```_

_When changing the DB schema, upon running app.py, respond "Y" to create the db_

### Testing Routes
You can use [Postman](https://www.postman.com/) to test your routes
- Endpoints definitions are located in the [Wiki](https://github.com/jayupad/My-Journal-Buddy/wiki)

### JWK Authorization
- To access a jwt_required protected endpoint, make to to include the access token in the authentication header. By default, this is done with an authorization header that looks like: ```{'Authorization': 'Bearer' + <access_token>}```
