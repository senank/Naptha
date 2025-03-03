FROM python:3.12-slim


WORKDIR /my_agent
COPY requirements_agent.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY my_agent .

EXPOSE 8080

CMD ["flask", "run", "--host=0.0.0.0"]
