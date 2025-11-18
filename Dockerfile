FROM python:3.11-alpine

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . . 

EXPOSE 5000

ENV FLASK_APP=main.py

# Run the Flask application using Gunicorn for production or Flask's built-in server for development
# For production, consider using Gunicorn:
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
# For development, you might use:
# CMD ["flask", "run"]
