import re
import psycopg2


class DeleteUser(object):
    def __init__(self, config: dict):
        kratos_config = config["kratos"]
        db_config = config["nobel_db"]

        if kratos_config is None or db_config is None:
            raise Exception("kratos config or db config missing")

        self.env = config["environment"]
        self._kratos_conn = self.__setup_connection(
            host=kratos_config["host"],
            database=kratos_config["database"],
            user=kratos_config["user"],
            password=kratos_config["password"],
        )
        self._db_conn = self.__setup_connection(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
        )

    def __setup_connection(self, host: str, database: str, user: str, password: str):
        return psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
        )

    def __mark_user_delete(self, email: str):
        try:
            kratos_id_null_query = f"UPDATE nobel_{self.env}.farm_user SET kratos_uuid = NULL WHERE email = '{email}';"

            cursor = self._db_conn.cursor()
            cursor.execute(kratos_id_null_query)
            cursor.commit()

            delete_email_query = (
                f"UPDATE nobel_{self.env}.farm_user SET email = 'USER DELETED' WHERE email = '{email}';"
            )

            cursor = self._db_conn.cursor()
            cursor.execute(kratos_id_null_query)
            cursor.commit()
        except Exception as ex:
            raise Exception(f"Nobel DB is throwing exception {str(ex)} while updating record {email}")

    def __remove_from_kratos(self, email: str):
        pass

    def __process_user(self, email: str):
        # Mark user as deleted in DB
        self.__mark_user_delete(email)

        # Remove user from Kratos
        self.__remove_from_kratos(email)

    def delete(self, list_of_users=list[str]):
        for user in list_of_users:
            try:
                if re.match(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$", user):
                    self.__process_user(user)
                else:
                    print(f"user email {user} is incorrect, doesn't follow standard email format")
            except Exception as ex:
                print(f"Exception thrown when trying to clean up user {user}    : {str(ex)}")
