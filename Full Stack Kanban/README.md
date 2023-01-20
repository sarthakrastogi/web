Instructions to start the app:

Run Ubuntu and run:

sarthak@Sarthak:~$ sudo service redis-server start


Run the following commands on Anaconda Prompts:

ad2> celery -A app.celery worker --pool=solo --loglevel=info

ad2> celery -A app.celery beat --max-interval 1 -l info

ad2> flask run


Run Mailhog, then go to http://localhost:8025/ to open the SMTP server.


Finally, open the main.html file to view the app