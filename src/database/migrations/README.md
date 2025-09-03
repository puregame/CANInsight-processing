## To Run Alembic

1. Open terminal in src folder.
2. Run the following commands: ` export PYTHONPATH=/workspace/src`
3. Include the following option in all alembic commands `-c database/alembic.ini`

### Point the config to a postgres DB
` bash
export DB_BACKEND=postgres DB_USER=root DB_PASSWORD=root DB_port=5432 DB_HOSTNAME=localhost DB_DATABASE=logserver_db
`

### To create a revision
`alembic -c database/alembic.ini revision --autogenerate -m "message here"`

### To update the db
`alembic -c database/alembic.ini upgrade head`
