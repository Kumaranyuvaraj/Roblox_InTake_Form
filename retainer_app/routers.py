class RetainerDatabaseRouter:
    """
    A router to control database operations for retainer_app models
    """
    
    route_app_labels = {'retainer_app'}

    def db_for_read(self, model, **hints):
        """Suggest the database to read from for retainer_app models."""
        if model._meta.app_label == 'retainer_app':
            return 'retainer_db'
        # Auth models needed in retainer_db for FK relationships
        elif model._meta.app_label in ['auth', 'contenttypes', 'admin', 'sessions'] and hints.get('instance') and hasattr(hints['instance'], '_state') and hints['instance']._state.db == 'retainer_db':
            return 'retainer_db'
        return None

    def db_for_write(self, model, **hints):
        """Suggest the database to write to for retainer_app models."""
        if model._meta.app_label == 'retainer_app':
            return 'retainer_db'
        # Auth models needed in retainer_db for FK relationships
        elif model._meta.app_label in ['auth', 'contenttypes', 'admin', 'sessions'] and hints.get('instance') and hasattr(hints['instance'], '_state') and hints['instance']._state.db == 'retainer_db':
            return 'retainer_db'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations if models are in the same database."""
        db_set = {'default', 'retainer_db'}
        if obj1._state.db in db_set and obj2._state.db in db_set:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Ensure that apps get created on the correct database."""
        if app_label == 'retainer_app':
            # retainer_app only goes to retainer_db
            return db == 'retainer_db'
        elif app_label in ['auth', 'contenttypes', 'admin', 'sessions']:
            # Core Django apps go to both databases
            return True
        elif app_label == 'roblex_app':
            # roblex_app only goes to default database
            return db == 'default'
        elif db == 'retainer_db':
            # No other apps should go to retainer_db
            return app_label in ['retainer_app', 'auth', 'contenttypes', 'admin', 'sessions']
        
        return None
