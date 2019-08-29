## Installation and Usage

```bash
sudo apt install virtualenv
sudo apt install npm
virtualenv -p pyhton3 .venv
source .venv/bin/activate
pip install -r requirments.txt
npm install
npm run build
python manage.py migrate
python manage.py createsuperuser admin
sudo ufw allow 8080
python manage.py runserver 0.0.0.0:8080
```
open in browser:
`0.0.0.0:8080/admin`
in other computers should use server ip instead of `0.0.0.0`
