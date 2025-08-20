import os

# ... other settings ...

# Add or modify the LOGGING configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',  # You can change to 'verbose' for more detail
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',  # Set root logger level to DEBUG
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'), # Default Django logs
            'propagate': False,
        },
        'core': {  # Logger for your 'core' app
            'handlers': ['console'],
            'level': 'DEBUG', # Set 'core' app logs to DEBUG
            'propagate': True, # Propagate to root (so you see 'core' messages)
        },
        'boxsdk': { # To make Box SDK less verbose unless specifically needed
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        }
    },
}

# ... other settings ... 