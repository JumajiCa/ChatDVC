# Use an official Python runtime as a parent image
FROM python:3.14-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Expose the port on which the Flask application will run
EXPOSE 5000

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run the Flask application using Gunicorn for production or Flask's built-in server for development
# For production, consider using Gunicorn:
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
# For development, you might use:
# CMD ["flask", "run"]