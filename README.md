## Requirements

pip install -r requirements.txt

Create environmental variables for Pushover client:

- USER_KEY
- API_TOKEN
- DEVICE

## Running tests

### Running all tests

`python testscases.py`

### Running an individual test
`python -m unittest testscases.Tests.testExcludedPhrasesWhenParentIsAReply`