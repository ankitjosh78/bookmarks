
**What is this project?**

This is a bookmarks application which can be used to bookmark and share images.
Uses can bookmark images, like them, follow each other and there is also an activity stream which shows all the recent actions across the website. It also uses Redis to count image views and rank them.

**How to run the project?**

0. Install Docker
1. Create and .env file which will have the following parameters depending on your setup:
   
   ```
   DOMAIN
   
   DATABASE_NAME
   
   DATABASE_USER
   
   DATABASE_PASSWORD
   
   EMAIL_BACKEND
   
   EMAIL_HOST
   
   EMAIL_HOST_USER
   
   EMAIL_HOST_USER_PASSWORD
   
   EMAIL_PORT
   
   EMAIL_USE_TLS
   ```

2. Setup your nginx.conf file with appropriate $host value
3. Run `docker-compose up --build -d`
4. Your site should be up and running at port 80 (default) and can be changed in nginx.conf.
5. Hello
