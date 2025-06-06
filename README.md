# Reimbly

## How to run this project locally

```
python3 -m venv .venv
source .venv/bin/activate

# in the .venv virtual environment
pip install google-adk
# verify adk version
pip show google-adk

# run project in web UI (select reimbly in web UI after executing the command)
adk web

# run tests
PYTHONPATH=. python -m unittest tests/test_agents.py

# exit virtual environment
deactivate
```



## TODOs
Currently, the data is stored in memory. In a real system, we need to:
- Use a database to store the reimbursement data
- Add caching for frequently accessed reports
- Implement real-time data updates
- Add more sophisticated visualization options
- Include export capabilities (CSV, PDF, etc.)