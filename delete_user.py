import psycopg2
import json
from typing import Any, Union
import uuid
import requests


class DeleteUser(object):
    def __init__(self, config_file_path: str):
        with open(config_file_path) as fp:
            config = json.load(fp)

        kratos_config = config["kratos"]
        db_config = config["nobel_db"]

        if kratos_config is None or db_config is None:
            raise Exception("kratos config or db config missing")

        self.env = config["env"]
        self.__kratos_conn = self.__setup_connection(
            host=kratos_config["host"],
            database=kratos_config["database"],
            user=kratos_config["user"],
            password=kratos_config["password"],
        )
        self.__db_conn = self.__setup_connection(
            host=db_config["host"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"],
        )
        self.kratos_url = config["kratos"]["url"]
        self.total_users = 0
        self.users_not_in_db = 0
        self.kratos_identities_count = 0
        self.kratos_deleted_users = 0
        self.total_users_deleted = 0
        self.total_db_users_marked_deleted = 0
        self.total_users_processed = 0

    def __setup_connection(self, host: str, database: str, user: str, password: str) -> Any:
        return psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
        )

    def __run_postgres_update(self, conn: Any, query: str) -> None:
        cursor = conn.cursor()
        cursor.execute(query=query)
        conn.commit()

    def __run_postgres_get(self, conn: Any, query: str) -> Any:
        cursor = conn.cursor()
        cursor.execute(query=query)
        return cursor.fetchall()

    def __is_user_present(self, conn: Any, email: str) -> bool:
        get_record_query = f"SELECT * FROM nobel_{self.env}.farm_user WHERE email = '{email}';"

        records = self.__run_postgres_get(conn, get_record_query)
        if len(records) == 1:
            return True

        return False

    def __mark_user_deleted(self, email: str) -> None:
        try:
            # fmt: off
            kratos_id_null_query = f"UPDATE nobel_{self.env}.farm_user SET kratos_uuid = NULL WHERE email = '{email}';"
            set_username_query = f"UPDATE nobel_{self.env}.farm_user SET username = '{email}' WHERE email = '{email}';"
            update_name_query = f"UPDATE nobel_{self.env}.farm_user SET name = 'USER IS DELETED, EMAIL PRESERVED IN username COLUMN' WHERE email = '{email}';"
            delete_email_query = f"UPDATE nobel_{self.env}.farm_user SET email = '{str(uuid.uuid4()).replace('-', '') + '@dummy.com'}' WHERE email ='{email}';"
            # fmt: on

            self.__run_postgres_update(self.__db_conn, kratos_id_null_query)
            self.__run_postgres_update(self.__db_conn, set_username_query)
            self.__run_postgres_update(self.__db_conn, update_name_query)
            self.__run_postgres_update(self.__db_conn, delete_email_query)
        except Exception as ex:
            raise Exception(f"Nobel DB is throwing exception {str(ex)} while marking record {email} for deletion")

    def __delete_kratos_user_as_admin(self, kratos_id: str) -> str:
        req_url = self.kratos_url

        response = requests.delete(req_url + kratos_id)

        if response.status_code != 204:
            raise Exception(
                f"Record {kratos_id} was not successfully deleted from Kratos, status code {response.status_code}"
            )

        self.kratos_deleted_users += 1

    def __get_kratos_id(self, email: str) -> Union[str, None]:
        try:
            # fmt: on
            get_kratos_email_query = f"SELECT id FROM public.identities WHERE traits->>'email' = '{email}';"
            # fmt: off

            records = self.__run_postgres_get(self.__kratos_conn, get_kratos_email_query)
            if len(records) == 1:
                return records[0][0]
        except Exception as ex:
            raise Exception(f"Exception thrown when retrieving kratos record for {email} {str(ex)}")

        return None

    def __remove_from_kratos(self, email: str) -> None:
        try:
            kratos_id = self.__get_kratos_id(email)

            if kratos_id:
                self.kratos_identities_count += 1
                print(f"Kratos id for the email {email} : {kratos_id}")
                self.__delete_kratos_user_as_admin(kratos_id)
                print(f"Kratos identity deleted for {email}")
        except Exception as ex:
            raise Exception(f"Removing record {email} from kratos is throwing exception {str(ex)}")

    def __process_user(self, email: str) -> None:
        # Remove user from Kratos
        self.__remove_from_kratos(email)

        if self.__is_user_present(self.__db_conn, email):
            self.total_users += 1
            # Mark user as deleted in DB
            self.__mark_user_deleted(email)
            print(f"DB record marked DELETED for {email}")
            self.total_db_users_marked_deleted += 1
        else:
            self.users_not_in_db += 1

        self.total_users_processed += 1

    def delete(self, users_list_file_path=str):
        user_emails_list = []
        with open(users_list_file_path) as fp:
            while line := fp.readline():
                user_email = line.strip("\r\n")
                user_emails_list.append(user_email)

        for user_email in user_emails_list:
            try:
                self.__process_user(user_email)
            except Exception as ex:
                print(f"Exception thrown for email {user_email}    : {str(ex)}")
                continue

        print(f"Total users in list                   :   {len(user_emails_list)}")
        print(f"Total users in DB                     :   {self.total_users}")
        print(f"Users not in DB                       :   {self.users_not_in_db}")
        print(f"Kratos identities                     :   {self.kratos_identities_count}")
        print(f"Kratos identities deleted             :   {self.kratos_deleted_users}")
        print(f"Total users marked for deletion in DB :   {self.total_db_users_marked_deleted}")
        print(f"Total users processed                 :   {self.total_users_processed}")
