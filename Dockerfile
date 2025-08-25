#Building a python image from the base
FROM python:3.12

#Making sure python doesn't have pyc files to save storage space
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

#This set the working directory of where your container will live
WORKDIR /app

#copy and install all requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

#copy the source codes into the working directory
COPY . .  

#Telling docker the command to run
CMD [ "daphne", "-b", "0.0.0.0", "-p", "8000", "chatbox.asgi:application" ]
