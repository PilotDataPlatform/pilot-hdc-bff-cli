# BFF-CLI

[![Python](https://img.shields.io/badge/python-3.8-brightgreen.svg)](https://www.python.org/)

## Getting Started
The backend for the command line interface.
### Built With
- Python
- FastAPI
## Getting Started

### Prerequisites
This project is using [Poetry](https://python-poetry.org/docs/#installation) to handle the dependencies.

    curl -sSL https://install.python-poetry.org | python3 -

### Installation & Quick Start

1. Clone the project.

       git clone https://github.com/PilotDataPlatform/sandbox.git

2. Install dependencies.

       poetry install

3. Install any OS level dependencies.

       apt install <foo>
       brew install <bar>

5. Add environment variables into `.env` in case it's needed. Use `.env.schema` as a reference.


6. Run any initial scripts, migrations or database seeders.

       poetry run alembic upgrade head

7. Run application.

       poetry run python run.py

### Startup using Docker

This project can also be started using [Docker](https://www.docker.com/get-started/).

1. To build and start the service within the Docker container run.

       docker compose up

2. Migrations should run automatically on previous step. They can also be manually triggered:

       docker compose run --rm alembic upgrade head

## Contribution

You can contribute the project in following ways:

* Report a bug
* Suggest a feature
* Open a pull request for fixing issues or adding functionality. Please consider
  using [pre-commit](https://pre-commit.com) in this case.
* For general guidelines how to contribute to the project, please take a look at the [contribution guides](CONTRIBUTING.md).

## Acknowledgements
The development of the HealthDataCloud open source software was supported by the EBRAINS research infrastructure, funded from the European Union's Horizon 2020 Framework Programme for Research and Innovation under the Specific Grant Agreement No. 945539 (Human Brain Project SGA3) and H2020 Research and Innovation Action Grant Interactive Computing E-Infrastructure for the Human Brain Project ICEI 800858.

This project has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101058516. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or other granting authorities. Neither the European Union nor other granting authorities can be held responsible for them.

![EU HDC Acknowledgement](https://hdc.humanbrainproject.eu/img/HDC-EU-acknowledgement.png)

