import argparse
from typing import Any
from delete_user import DeleteUser


def delete_users(args: Any):
    try:
        delete_user = DeleteUser(args.config_file)

        delete_user.delete(args.user_list)
    except Exception as ex:
        print(f"Exception occurs : {str(ex)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--config_file", required=True, help="Json file ")
    parser.add_argument("--user_list", required=True, help="File with list of users")

    args = parser.parse_args()

    delete_users(args=args)
