# E-commsite_D

A Django-based ecommerce site.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The local development settings use SQLite. Open http://127.0.0.1:8000/ after
starting the server. Product records are stored in the database; media files
must be present under `media/` for product images to display.

## Project layout

- `ecommers/` - Django settings and URL configuration
- `accounts/` - registration, login, profiles, and cart
- `product/` - product catalog and product pages
- `home/` - storefront homepage and search
- `base/` - shared models and email helpers
- `templates/` - Django HTML templates
- `public/static/` - CSS, JavaScript, fonts, and static images
- `media/` - uploaded product and category images
- `product_data.json` - sample product data fixture

For production, configure the required environment variables in a local,
untracked environment file. Do not store credentials in the repository.
