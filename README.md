
**What is this project?**

This is a bookmarks application which can be used to bookmark and share images.
Uses can bookmark images, like them, follow each other and there is also an activity stream which shows all the recent actions across the website. It also uses Redis to count image views and rank them.

**How to run the project?**

0. Activate your virtual environment(suggested)
1. pip install -r requirements.txt
2. Install Docker
3. docker pull redis
4. docker run -it --rm --name redis -p 6379:6379 redis
5. python manange.py makemigrations
6. python manage.py migrate
7. python manage.py runserver
