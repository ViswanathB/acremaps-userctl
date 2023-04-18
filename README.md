# acremaps-userctl
Delete acremaps users


# How DeleteUser works
1. Verify User in Nobel DB
2. If user is present, mark him/her for DELETION
 a. SET Kratos UUID col NULL
 b. SET username to email
 c. SET name =  'USER IS DELETED, EMAIL PRESERVED IN username COLUMN'
 d. SET email = a new UUID, email has to be unique and doesn't let me make it as NULL

Kratos ID will be removed irrespective of user existing in Nobel DB