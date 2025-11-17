To install the requirements:

pip install -r requirements.txt

then u can launch main.py to launch the server using 

uvicorn main:app --reload --port 8000

--reload enables automatic reloading
--port specifies the port number (default is 8000) so u can just change it if needed.
Make sure you have Python and pip installed on your system before running the above commands.
You can access the server at http://localhost:8000 once it's running.
