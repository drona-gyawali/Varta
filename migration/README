# Database Migrations

This project requires **PostgreSQL** as the database and uses **Alembic** for managing schema migrations.

## How to Run Migrations

1. Ensure you have PostgreSQL installed and running.
2. Install the required Python dependencies (including Alembic) by running:
    ```
    pip install -r requirements.txt
    ```
3. Configure your database connection settings in `.env` or your project's configuration file.
4. To apply all pending migrations, run:
    ```
    alembic upgrade head
    ```
5. To create a new migration after making changes to your models, use:
    ```
    alembic revision --autogenerate -m "Describe your change"
    ```
6. Review and test your migrations before applying them to production.

## Notes

- Always back up your database before running migrations.
- Review migration files for accuracy.
- For more details, refer to the [Alembic documentation](https://alembic.sqlalchemy.org/).
