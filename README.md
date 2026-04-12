### Start virtual env for python 

```bash
source .venv/bin/activate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Run langgraph development
```bash
langgraph dev
```

### Run FastApi production
```
uv run uvicorn api.main:app --reload
```

