FROM python:3.12-slim

COPY requirements.build.txt ./
RUN pip install --disable-pip-version-check --no-cache-dir \
    -r requirements.build.txt

COPY requirements.txt ./
RUN pip install --disable-pip-version-check --no-cache-dir \
    -r requirements.txt

COPY requirements.dev.txt ./
RUN pip install --disable-pip-version-check --no-cache-dir \
    -r requirements.txt \
    -r requirements.dev.txt

COPY data ./data
COPY data_ai_bot ./data_ai_bot
COPY setup.cfg ./

CMD ["python3", "-m", "data_ai_bot"]
