# acremaps-userctl
Delete acremaps users


# How DeleteUser works
Verify User is present in Nobel DB -> If user is present, mark him/her for DELETION as follows
  1. SET Kratos UUID col NULL
  2. SET username to email
  3. SET name =  'USER IS DELETED, EMAIL PRESERVED IN username COLUMN'
  4. SET email = a new UUID, email has to be unique and doesn't let me make it as NULL

Kratos ID will be removed irrespective of user existing in Nobel DB