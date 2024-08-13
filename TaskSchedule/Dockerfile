FROM cgr.dev/chainguard/python:latest-dev as dev

WORKDIR /app

RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

FROM cgr.dev/chainguard/python:latest

WORKDIR /app

COPY /app /app/app
COPY --from=dev /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# ENTRYPOINT ["uvicorn", "app.main:app", "--port", "8000"]

ENTRYPOINT ["fastapi", "run", "app/main.py", "--port", "8000"]
