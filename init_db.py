from wissio_app import app, db
import sys

# Force SQLite DB URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wissio.db'
print('DEBUG: Overridden DB URI:', app.config.get('SQLALCHEMY_DATABASE_URI'))
sys.stdout.flush()

with app.app_context():
    db.create_all()
print('DEBUG: DB init completed')
sys.stdout.flush()
