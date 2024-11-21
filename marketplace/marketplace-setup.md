# Marketplace App - Initial Setup

This document outlines the process to create the initial categories for your Marketplace application using Django's shell.

## Steps to Add Categories

1. Open the Django shell by running the following command:

    ```bash
    python manage.py shell
    ```

2. Import the `Category` model from the `marketplace` app:

    ```python
    from marketplace.models import Category
    ```

3. Create the following categories:

    ```python
    Category.objects.create(name='Electronics')
    Category.objects.create(name='Books')
    Category.objects.create(name='Fashion')
    Category.objects.create(name='Furniture')
    Category.objects.create(name='Sports')
    ```

These categories will be available in your marketplace for users to filter and browse products.

## Notes

- Ensure that your database is properly set up and migrations have been run before adding data.
- You can modify or add more categories as per the requirements of your application.
