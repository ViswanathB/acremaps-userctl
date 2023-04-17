import json
import psycopg2


class DeleteUser(object):
    def __init__(self, config: dict):
        kratos_config = config["kratos"]
        db_config = config["nobel_db"]

        if kratos_config is None or db_config is None:
            raise Exception("kratos config or db config missing")

        self._kratos_conn = self._setup_connection(
            host=kratos_config["host"],
            database=kratos_config["database"],
            user=kratos_config["user"],
            password=kratos_config["password"],
        )
        self._db_conn = self._setup_connection(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
        )

    def _setup_connection(self, host: str, database: str, user: str, password: str):
        return psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
        )

    def delete(self, list_of_users=list[str]):
        for user in list_of_users:
            print(user)
