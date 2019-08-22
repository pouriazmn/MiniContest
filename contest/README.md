## Installation and Usage

```bash
sudo apt install virtualenv
virtualenv -p pyhton3 env
source env/bin/activate
pip install -r requirments.txt
python manage.py migrate
python manage.py createsuperuser admin
sudo ufw allow 8080
python manage.py runserver 0.0.0.0:8080
```
open in browser:
`0.0.0.0:8080/admin`
in other computers should use server ip instead of `0.0.0.0`
