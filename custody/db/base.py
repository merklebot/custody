# Import all the models, so that Base has them before being
# imported by Alembic

from custody.db.base_class import Base

from .models.user import *
from .models.storage.key import *
from .models.storage.content import *
