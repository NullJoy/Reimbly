# Reimbly

## How to run this project locally
Update `.env` file with your google cloud project id and location.

```
python3 -m venv .venv
source .venv/bin/activate

# in the .venv virtual environment
pip install -r requirements.txt
# verify adk version
pip show google-adk

# run project in web UI (select reimbly in web UI after executing the command)
adk web

# run tests
PYTHONPATH=. python -m unittest tests/test_agents.py

# exit virtual environment
deactivate
```

## TESTS - Need to remove
- To test with the notificatino, will need to switch user email to the targetted email address.


## TODOs
Currently, the data is stored in memory. In a real system, we need to:
- Use a database to store the reimbursement data
- Add caching for frequently accessed reports
- Implement real-time data updates
- Add more sophisticated visualization options
- Include export capabilities (CSV, PDF, etc.)